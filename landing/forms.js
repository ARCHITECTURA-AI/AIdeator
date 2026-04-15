(function () {
  function setStatus(el, message, isError) {
    if (!el) return;
    el.textContent = message;
    el.style.color = isError ? "#ff9b9b" : "#8bffcc";
  }

  async function submitJson(endpoint, payload) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Submission failed");
    }
    return response;
  }

  function serializeForm(form) {
    const data = new FormData(form);
    const out = {};
    for (const [key, value] of data.entries()) {
      if (key === "website") continue;
      out[key] = String(value).trim();
    }
    return out;
  }

  function wireForm(formId, endpointKey) {
    const form = document.getElementById(formId);
    if (!form) return;
    const status = form.querySelector('[data-form-status="true"]');

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const cfg = window.__SITE_CONFIG || {};
      const endpoint = cfg.forms && cfg.forms[endpointKey];
      if (!endpoint) {
        setStatus(status, "Form endpoint is not configured.", true);
        return;
      }

      const honeypot = form.querySelector('input[name="website"]');
      if (honeypot && honeypot.value.trim()) {
        setStatus(status, "Submitted.", false);
        form.reset();
        return;
      }

      const payload = serializeForm(form);
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      try {
        await submitJson(endpoint, payload);
        setStatus(status, "Thanks, submission received.", false);
        form.reset();
      } catch (error) {
        setStatus(status, "Submission failed. Check endpoint and try again.", true);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function init() {
    wireForm("waitlist-form", "waitlistEndpoint");
    wireForm("contact-form", "contactEndpoint");
  }

  document.addEventListener("site-config-loaded", init);
  if (window.__SITE_CONFIG) init();
})();
