import { useCallback, useEffect, useRef, useState } from 'react'

import { storage } from '@/lib/storage'
import type {
  ChatUIMessage,
  AgentHandoffContext,
  SSEEventType,
  SourceCitation,
  ToolCallState,
} from '@/types/agent'

interface UseSSEChatOptions {
  workspaceId: string | null
  onError?: (message: string) => void
}

export interface UseSSEChatReturn {
  messages: ChatUIMessage[]
  isStreaming: boolean
  thinking: string
  sessionId: string | null
  sendMessage: (
    message: string,
    sessionId?: string | null,
    reasoningMode?: string,
    handoffContext?: AgentHandoffContext | null,
  ) => void
  clearMessages: () => void
  setMessages: React.Dispatch<React.SetStateAction<ChatUIMessage[]>>
  setSessionId: React.Dispatch<React.SetStateAction<string | null>>
  abort: () => void
}

export function useSSEChat({ workspaceId, onError }: UseSSEChatOptions): UseSSEChatReturn {
  const [messages, setMessages] = useState<ChatUIMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [thinking, setThinking] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)

  const contentRef = useRef('')
  const thinkingRef = useRef('')
  const toolCallsRef = useRef<ToolCallState[]>([])
  const sourcesRef = useRef<SourceCitation[]>([])
  const followUpsRef = useRef<string[]>([])
  const xhrRef = useRef<XMLHttpRequest | null>(null)
  const cursorRef = useRef(0)

  // Reset state when the workspace changes.
  useEffect(() => {
    if (xhrRef.current) {
      xhrRef.current.abort()
      xhrRef.current = null
    }
    setMessages([])
    setIsStreaming(false)
    setThinking('')
    setSessionId(null)
    contentRef.current = ''
    thinkingRef.current = ''
    toolCallsRef.current = []
    sourcesRef.current = []
    followUpsRef.current = []
    cursorRef.current = 0
  }, [workspaceId])

  const flushAssistant = useCallback(() => {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last && last.role === 'assistant' && last.isStreaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...last,
            content: contentRef.current,
            thinking: thinkingRef.current || undefined,
            toolCalls: toolCallsRef.current.length > 0 ? [...toolCallsRef.current] : undefined,
            sources: sourcesRef.current.length > 0 ? [...sourcesRef.current] : undefined,
            followUps: followUpsRef.current.length > 0 ? [...followUpsRef.current] : undefined,
          },
        ]
      }
      return prev
    })
    setThinking(thinkingRef.current)
  }, [])

  const finishStream = useCallback(() => {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last && last.role === 'assistant' && last.isStreaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...last,
            content: contentRef.current,
            thinking: thinkingRef.current || undefined,
            toolCalls: toolCallsRef.current.length > 0 ? [...toolCallsRef.current] : undefined,
            sources: sourcesRef.current.length > 0 ? [...sourcesRef.current] : undefined,
            followUps: followUpsRef.current.length > 0 ? [...followUpsRef.current] : undefined,
            isStreaming: false,
          },
        ]
      }
      return prev
    })
    setIsStreaming(false)
    setThinking('')
  }, [])

  const handleEvent = useCallback(
    (eventType: SSEEventType, data: Record<string, unknown>) => {
      switch (eventType) {
        case 'stream_start': {
          const sid = data.session_id as string
          if (sid) setSessionId(sid)
          break
        }
        case 'message_delta': {
          contentRef.current += data.content as string
          flushAssistant()
          break
        }
        case 'thinking_delta': {
          thinkingRef.current += data.content as string
          flushAssistant()
          break
        }
        case 'tool_start': {
          const tc: ToolCallState = {
            callId: data.call_id as string,
            toolName: data.tool_name as string,
            inputs: (data.inputs as Record<string, unknown>) || {},
            isRunning: true,
          }
          toolCallsRef.current = [...toolCallsRef.current, tc]
          flushAssistant()
          break
        }
        case 'tool_end': {
          const callId = data.call_id as string
          toolCallsRef.current = toolCallsRef.current.map((tc) =>
            tc.callId === callId ? { ...tc, output: data.output as string, isRunning: false } : tc,
          )
          flushAssistant()
          break
        }
        case 'follow_ups': {
          followUpsRef.current = data.questions as string[]
          flushAssistant()
          break
        }
        case 'source_citations': {
          const srcs = data.sources as Array<Record<string, unknown>>
          sourcesRef.current = srcs.map((s) => ({
            title: (s.title as string) ?? '',
            chunk: (s.chunk as string) ?? '',
            score: (s.score as number) ?? 0,
            documentId: (s.document_id as string) ?? '',
          }))
          flushAssistant()
          break
        }
        case 'stream_end': {
          finishStream()
          break
        }
        case 'error': {
          finishStream()
          onError?.((data.message as string) || 'An error occurred')
          break
        }
      }
    },
    [flushAssistant, finishStream, onError],
  )

  const parseSSEChunk = useCallback(
    (text: string) => {
      const chunk = text.slice(cursorRef.current)
      cursorRef.current = text.length
      const lines = chunk.split('\n')
      let currentEvent: SSEEventType | null = null
      for (const line of lines) {
        if (line.startsWith(': ping')) continue
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim() as SSEEventType
        } else if (line.startsWith('data: ') && currentEvent) {
          try {
            const data = JSON.parse(line.slice(6))
            handleEvent(currentEvent, data)
          } catch {
            // partial JSON
          }
          currentEvent = null
        }
      }
    },
    [handleEvent],
  )

  const sendMessage = useCallback(
    (
      message: string,
      existingSessionId?: string | null,
      reasoningMode: string = 'balanced',
      handoffContext?: AgentHandoffContext | null,
    ) => {
      if (isStreaming || !workspaceId) return

      const userMsg: ChatUIMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: Date.now(),
        source: 'agent',
      }
      const assistantMsg: ChatUIMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        source: 'agent',
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setThinking('')

      contentRef.current = ''
      thinkingRef.current = ''
      toolCallsRef.current = []
      sourcesRef.current = []
      followUpsRef.current = []
      cursorRef.current = 0

      const xhr = new XMLHttpRequest()
      xhrRef.current = xhr

      xhr.open('POST', `/api/workspaces/${workspaceId}/agent/chat`)
      xhr.setRequestHeader('Content-Type', 'application/json')
      const token = storage.getToken()
      if (token && token !== 'undefined' && token !== 'null') {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      xhr.onprogress = () => parseSSEChunk(xhr.responseText)
      xhr.onloadend = () => {
        if (xhr.responseText.length > cursorRef.current) {
          parseSSEChunk(xhr.responseText)
        }
        if (xhr.status >= 400 && !xhr.responseText.includes('event:')) {
          try {
            const body = JSON.parse(xhr.responseText) as { detail?: string }
            onError?.(body.detail || `Chat request failed (${xhr.status})`)
          } catch {
            onError?.(`Chat request failed (${xhr.status})`)
          }
        }
        finishStream()
        xhrRef.current = null
      }
      xhr.onerror = () => {
        finishStream()
        onError?.('Connection failed')
        xhrRef.current = null
      }

      const sid = existingSessionId ?? sessionId
      xhr.send(
        JSON.stringify({
          message,
          session_id: sid,
          reasoning_mode: reasoningMode,
          handoff_context: !sid && handoffContext ? handoffContext : undefined,
        }),
      )
    },
    [isStreaming, workspaceId, sessionId, parseSSEChunk, finishStream, onError],
  )

  const abort = useCallback(() => {
    if (xhrRef.current) {
      xhrRef.current.abort()
      xhrRef.current = null
    }
    finishStream()
  }, [finishStream])

  const clearMessages = useCallback(() => {
    abort()
    setMessages([])
    setSessionId(null)
    contentRef.current = ''
    thinkingRef.current = ''
    toolCallsRef.current = []
    sourcesRef.current = []
    followUpsRef.current = []
    cursorRef.current = 0
  }, [abort])

  return {
    messages,
    isStreaming,
    thinking,
    sessionId,
    sendMessage,
    clearMessages,
    setMessages,
    setSessionId,
    abort,
  }
}
