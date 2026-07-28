(() => {
  const HEIGHT_MESSAGE = "corpus-design-surface-height"
  const HEIGHT_REQUEST = "corpus-design-surface-height-request"

  const reportHeight = () => {
    const surface = [...document.querySelectorAll(".surface")]
      .find((candidate) => getComputedStyle(candidate).display !== "none")

    if (!(surface instanceof HTMLElement)) return

    const bodyTop = document.body.getBoundingClientRect().top
    const surfaceBottom = surface.getBoundingClientRect().bottom
    const paddingBottom = Number.parseFloat(getComputedStyle(document.body).paddingBottom) || 0
    const height = Math.ceil(surfaceBottom - bodyTop + paddingBottom)

    parent.postMessage({ type: HEIGHT_MESSAGE, height }, "*")
  }

  const start = () => {
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(reportHeight)
      document.querySelectorAll(".surface").forEach((surface) => observer.observe(surface))
    }

    reportHeight()
    requestAnimationFrame(reportHeight)
  }

  window.addEventListener("message", (event) => {
    if (event.data?.type === HEIGHT_REQUEST) reportHeight()
  })
  window.addEventListener("hashchange", reportHeight)

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true })
  } else {
    start()
  }
})()
