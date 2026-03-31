const toggleButtons = document.querySelectorAll(".citation-toggle");
for (const button of toggleButtons) {
  button.addEventListener("click", () => {
    const targetId = button.getAttribute("data-target");
    if (!targetId) return;
    const node = document.getElementById(targetId);
    if (!node) return;
    node.classList.toggle("hidden");
  });
}
