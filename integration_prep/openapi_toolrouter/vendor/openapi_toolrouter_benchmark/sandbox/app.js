let lastDecision = null

function value(id) {
  return document.getElementById(id).value
}

function output(payload) {
  document.getElementById('output').textContent = JSON.stringify(payload, null, 2)
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return response.json()
}

document.getElementById('route').addEventListener('click', async () => {
  const payload = {
    tenant_id: value('tenant'),
    integration_id: value('integration'),
    query: value('query'),
    guardrails: {
      mode: value('mode'),
      auto_route_confidence_threshold: 0,
      route_margin_threshold: 0,
      unsafe_write_threshold: 0,
    },
    conversation_context: [
      {
        sandbox_signup_allowed: document.getElementById('signup').checked,
        sandbox_credentials_present: Boolean(value('username') || value('password')),
      },
    ],
  }
  lastDecision = await postJson('/api/route', payload)
  output(lastDecision)
})

document.getElementById('positive').addEventListener('click', async () => {
  if (!lastDecision) return
  const selected = lastDecision.selected_endpoint || lastDecision.top_candidates?.[0]?.endpoint_id || null
  output(await postJson('/api/feedback', {
    tenant_id: value('tenant'),
    integration_id: value('integration'),
    query: value('query'),
    decision_type: lastDecision.decision_type,
    selected_endpoint: lastDecision.selected_endpoint,
    user_selected_endpoint: selected,
    sandbox_credentials: {
      username: value('username'),
      password: value('password'),
    },
    label_quality: 'explicit',
  }))
})

document.getElementById('reject').addEventListener('click', async () => {
  if (!lastDecision) return
  output(await postJson('/api/feedback', {
    tenant_id: value('tenant'),
    integration_id: value('integration'),
    query: value('query'),
    decision_type: lastDecision.decision_type,
    rejected_endpoints: lastDecision.top_candidates?.[0]?.endpoint_id ? [lastDecision.top_candidates[0].endpoint_id] : [],
    label_quality: 'explicit',
  }))
})
