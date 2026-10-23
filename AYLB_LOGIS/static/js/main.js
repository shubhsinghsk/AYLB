(() => {
  "use strict";

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initHeader() {
    const nav = document.getElementById("siteNav");
    if (!nav) return;
    const update = () => nav.classList.toggle("is-scrolled", window.scrollY > 18);
    update();
    window.addEventListener("scroll", update, { passive: true });
  }

  function initRevealEffects() {
    const targets = document.querySelectorAll(".wow");
    if (!targets.length) return;
    targets.forEach((element) => {
      element.classList.add("reveal-on-scroll");
      const delay = Number.parseFloat(element.dataset.wowDelay || "0");
      if (Number.isFinite(delay) && delay > 0) {
        element.style.setProperty("--reveal-delay", `${Math.min(delay, 0.8)}s`);
      }
    });
    document.documentElement.classList.add("motion-ready");
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      targets.forEach((element) => element.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries, currentObserver) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    targets.forEach((element) => observer.observe(element));
  }

  function animateCount(element) {
    if (element.dataset.counted === "true") return;
    const target = Number.parseInt(element.dataset.count, 10);
    if (!Number.isFinite(target)) return;
    element.dataset.counted = "true";
    const suffix = element.dataset.suffix || "";
    if (prefersReducedMotion) {
      element.textContent = `${target.toLocaleString()}${suffix}`;
      return;
    }
    const duration = 1100;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = `${Math.round(target * eased).toLocaleString()}${suffix}`;
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function initCountUps() {
    const counters = document.querySelectorAll("span[data-count]");
    if (!counters.length) return;
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      counters.forEach(animateCount);
      return;
    }
    const observer = new IntersectionObserver((entries, currentObserver) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          currentObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.55 });
    counters.forEach((counter) => observer.observe(counter));
  }

  function initNetworkExplorer() {
    const network = document.getElementById("network-container");
    const output = document.getElementById("networkSelection");
    if (!network || !output) return;
    const items = [...network.querySelectorAll(".network-item")];
    const maxCount = Math.max(...items.map((item) => Number(item.dataset.count) || 0), 1);

    items.forEach((item) => {
      const count = Number(item.dataset.count) || 0;
      const label = item.querySelector("span");
      const bar = document.createElement("span");
      bar.className = "network-bar";
      bar.setAttribute("aria-hidden", "true");
      bar.style.setProperty("--bar-progress", `${(count / maxCount) * 100}%`);
      const countLabel = document.createElement("span");
      countLabel.className = "network-count";
      countLabel.textContent = count.toLocaleString();
      countLabel.setAttribute("aria-hidden", "true");
      item.append(bar, countLabel);
      item.setAttribute("aria-label", `${label.textContent.trim()}, ${count} branches`);
      item.addEventListener("click", () => {
        items.forEach((region) => {
          region.classList.remove("is-selected");
          region.setAttribute("aria-pressed", "false");
        });
        item.classList.add("is-selected");
        item.setAttribute("aria-pressed", "true");
        output.innerHTML = `<strong>${count.toLocaleString()} branches</strong><span> in ${label.textContent.trim()}</span>`;
      });
    });

    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      items.forEach((item) => item.classList.add("is-visible"));
    } else {
      const observer = new IntersectionObserver((entries, currentObserver) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            currentObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      items.forEach((item) => observer.observe(item));
    }
  }

  function initServiceSearch() {
    const input = document.getElementById("serviceSearch");
    const count = document.getElementById("serviceSearchCount");
    const content = document.getElementById("serviceTabContent");
    if (!input || !count || !content) return;

    const panes = [...content.querySelectorAll(".tab-pane")];
    const filterActivePane = () => {
      const pane = content.querySelector(".tab-pane.active");
      if (!pane) return;
      const cards = [...pane.querySelectorAll("[data-service-card]")];
      const query = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach((card) => {
        const matches = card.textContent.toLocaleLowerCase().includes(query);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      count.textContent = query ? `${visible} ${visible === 1 ? "service" : "services"}` : `${cards.length} services`;
      let empty = pane.querySelector(".service-empty-state");
      if (!empty) {
        empty = document.createElement("p");
        empty.className = "service-empty-state";
        empty.textContent = "No services match your search. Try another term.";
        empty.setAttribute("role", "status");
        pane.appendChild(empty);
      }
      empty.hidden = visible !== 0;
    };

    input.addEventListener("input", filterActivePane);
    document.querySelectorAll("#serviceTabs [data-bs-toggle='pill']").forEach((tab) => {
      tab.addEventListener("shown.bs.tab", () => {
        input.value = "";
        filterActivePane();
      });
    });
    panes.forEach((pane) => pane.querySelectorAll("[data-service-card]").forEach((card) => { card.hidden = false; }));
    filterActivePane();
  }

  function initContactFormFeedback() {
    const form = document.querySelector("form.contact-form");
    if (!form) return;
    form.addEventListener("submit", () => {
      const button = form.querySelector("[type='submit']");
      if (!button) return;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Sending…';
    });
  }

  function initApplicationFormNotice() {
    const form = document.querySelector("[data-application-form]");
    const status = document.getElementById("applicationStatus");
    if (!form || !status) return;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      status.hidden = false;
      status.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "nearest" });
    });
  }

  function initServiceCounters() {
    document.querySelectorAll(".counter[data-target]").forEach((counter) => {
      const target = Number(counter.dataset.target);
      if (!Number.isFinite(target)) return;
      if (prefersReducedMotion || !("IntersectionObserver" in window)) {
        counter.textContent = target.toLocaleString();
        return;
      }
      const observer = new IntersectionObserver((entries, currentObserver) => {
        if (!entries[0].isIntersecting) return;
        let value = 0;
        const increment = Math.max(1, Math.ceil(target / 70));
        const timer = window.setInterval(() => {
          value = Math.min(value + increment, target);
          counter.textContent = value.toLocaleString();
          if (value === target) window.clearInterval(timer);
        }, 18);
        currentObserver.disconnect();
      }, { threshold: 0.5 });
      observer.observe(counter);
    });
  }

  function initImageModal() {
    const imageModal = document.getElementById("imageModal");
    if (!imageModal) return;
    imageModal.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      if (!trigger) return;
      const image = imageModal.querySelector(".modal-body img");
      const title = imageModal.querySelector(".modal-title");
      if (image) image.src = trigger.getAttribute("data-img-src") || "";
      if (title) title.textContent = trigger.getAttribute("data-img-title") || "Service image";
    });
  }

  function initTeamCarousel() {
    const carousel = document.querySelector(".teamSwiper");
    if (!carousel || typeof window.Swiper !== "function") return;
    new window.Swiper(carousel, {
      slidesPerView: 1,
      spaceBetween: 20,
      loop: true,
      autoplay: prefersReducedMotion ? false : { delay: 4200, disableOnInteraction: false, pauseOnMouseEnter: true },
      navigation: { nextEl: carousel.querySelector(".swiper-button-next"), prevEl: carousel.querySelector(".swiper-button-prev") },
      breakpoints: { 640: { slidesPerView: 2 }, 1024: { slidesPerView: 3 } }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHeader();
    initRevealEffects();
    initCountUps();
    initNetworkExplorer();
    initServiceSearch();
    initContactFormFeedback();
    initApplicationFormNotice();
    initServiceCounters();
    initImageModal();
    initTeamCarousel();
  });
})();
