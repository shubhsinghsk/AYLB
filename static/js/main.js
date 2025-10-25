console.log('AYLB Logistics site loaded');
// Animate Network Bars on Scroll
function animateNetworkBars() {
  const bars = document.querySelectorAll(".network-item");

  bars.forEach((bar) => {
    const count = parseInt(bar.getAttribute("data-count"));
    const percentage = Math.min((count / 12) * 100, 100); // max 12 -> full bar

    // Animate width when visible
    const rect = bar.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100 && bar.dataset.animated !== "true") {
      bar.querySelector("span").style.zIndex = "3";
      bar.style.overflow = "hidden";
      bar.dataset.animated = "true";
      bar.querySelector("span").style.color = "#003366";
      bar.style.backgroundColor = "#e9f5ff";
      bar.style.transition = "all 0.3s ease-in-out";
      bar.style.position = "relative";

      setTimeout(() => {
        bar.style.setProperty("--bar-width", percentage + "%");
        bar.querySelector("span").style.color = "#003366";
        bar.style.background = `linear-gradient(90deg, #cce6ff ${percentage}%, #e9f5ff ${percentage}%)`;
      }, 150);
    }
  });
}

window.addEventListener("scroll", animateNetworkBars);
window.addEventListener("load", animateNetworkBars);
