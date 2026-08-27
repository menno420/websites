"use strict";

document.querySelectorAll("form[data-submitting-label]").forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button[type='submit']");
    if (!button || button.disabled) return;
    button.disabled = true;
    button.textContent = form.dataset.submittingLabel || "submitting…";
    button.setAttribute("aria-busy", "true");
  });
});
