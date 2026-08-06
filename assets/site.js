document.documentElement.classList.remove("no-js");

document.addEventListener("DOMContentLoaded", () => {
  const topNav = document.querySelector(".top-nav");
  const topNavLinks = topNav ? Array.from(topNav.querySelectorAll("a")) : [];
  if (topNav && !topNavLinks.some((link) => link.textContent.trim() === "과목별학원")) {
    const homeLink = topNavLinks.find((link) => link.textContent.trim() === "홈");
    const nationwideLink = topNavLinks.find((link) => link.textContent.trim() === "전국학원");
    if (homeLink) {
      const subjectLink = document.createElement("a");
      subjectLink.href = homeLink.getAttribute("href").replace(/index\.html(?:#.*)?$/, "과목별학원/index.html");
      subjectLink.textContent = "과목별학원";
      if (decodeURI(window.location.pathname).includes("/과목별학원/")) {
        subjectLink.classList.add("active");
      }
      topNav.insertBefore(subjectLink, nationwideLink || null);
    }
  }

  const revealItems = document.querySelectorAll(".reveal");

  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -40px 0px" }
    );

    revealItems.forEach((item) => observer.observe(item));
  }

  const details = document.querySelectorAll(".faq-list details");
  details.forEach((item) => {
    item.addEventListener("toggle", () => {
      if (!item.open) return;
      details.forEach((other) => {
        if (other !== item) other.open = false;
      });
    });
  });

  const subjectDirectory = document.querySelector("[data-subject-directory]");
  if (subjectDirectory) {
    const search = subjectDirectory.querySelector("[data-subject-search]");
    const status = subjectDirectory.querySelector("[data-subject-search-status]");
    const cards = Array.from(subjectDirectory.querySelectorAll("[data-subject-town]"));
    const districts = Array.from(subjectDirectory.querySelectorAll("[data-subject-district]"));
    const regions = Array.from(subjectDirectory.querySelectorAll("[data-subject-region]"));

    const normalize = (value) => value.toLocaleLowerCase("ko-KR").replace(/\s+/g, "");
    const updateDirectory = () => {
      const query = normalize(search.value.trim());
      let visibleCount = 0;

      cards.forEach((card) => {
        const matches = !query || normalize(card.dataset.search || card.textContent).includes(query);
        card.hidden = !matches;
        if (matches) visibleCount += 1;
      });

      districts.forEach((district) => {
        district.hidden = !Array.from(district.querySelectorAll("[data-subject-town]")).some((card) => !card.hidden);
      });

      regions.forEach((region) => {
        const hasResult = Array.from(region.querySelectorAll("[data-subject-town]")).some((card) => !card.hidden);
        region.hidden = !hasResult;
        if (query && hasResult) region.open = true;
      });

      status.textContent = query ? `${visibleCount}개 지역 검색 결과` : `전체 ${cards.length}개 지역`;
    };

    search.addEventListener("input", updateDirectory);
  }
});
