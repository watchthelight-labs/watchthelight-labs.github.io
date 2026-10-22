// <wtl> project: watchthelight-labs.github.io | file: src/copy.js | author: watchthelight </wtl>
// "Copy" buttons next to the clone line.
document.querySelectorAll("[data-copy]").forEach((b) => {
  b.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(b.getAttribute("data-copy"));
      const t = b.textContent;
      b.textContent = "copied";
      setTimeout(() => (b.textContent = t), 1400);
    } catch (e) {
      b.textContent = "select it";
    }
  });
});
