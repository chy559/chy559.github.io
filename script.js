const articles = {
  tech: [],
  galgame: [],
  nongalgame: []
};

const placeholders = {
  tech: {
    title: "技术文章还在准备中",
    text: "之后这里会放前端、工程化、项目复盘和学习笔记。"
  },
  galgame: {
    title: "Galgame 记录还在准备中",
    text: "这里会收纳视觉小说感想、角色记录、路线整理和推荐。"
  },
  nongalgame: {
    title: "非 Galgame 记录还在准备中",
    text: "这里会放动作、RPG、独立游戏以及其他游玩碎片。"
  }
};

let previousRoute = "home";

function renderLists() {
  document.querySelectorAll(".article-list").forEach((list) => {
    const category = list.dataset.category;
    const items = articles[category] || [];

    if (!items.length) {
      const empty = placeholders[category];
      list.innerHTML = `
        <article class="empty-card">
          <p class="eyebrow">${category}</p>
          <h2>${empty.title}</h2>
          <p>${empty.text}</p>
        </article>
      `;
      return;
    }

    list.innerHTML = items
      .map(
        (article) => `
          <article class="article-card" tabindex="0" data-article-id="${article.id}">
            <span class="article-tag">${article.category}</span>
            <div>
              <h2>${article.title}</h2>
              <p>${article.summary}</p>
            </div>
            <span class="article-arrow" aria-hidden="true">→</span>
          </article>
        `
      )
      .join("");
  });
}

function setRoute(route) {
  const target = document.querySelector(`#view-${route}`);
  if (!target) return;

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("view-active", view === target);
  });

  document.querySelectorAll("[data-route]").forEach((link) => {
    link.classList.toggle("nav-active", link.dataset.route === route);
  });

  if (route !== "article") previousRoute = route;
  window.history.replaceState(null, "", `#${route}`);
}

function openArticle(article) {
  document.querySelector("#detail-category").textContent = article.category;
  document.querySelector("#detail-title").textContent = article.title;
  document.querySelector("#detail-summary").textContent = article.summary;
  setRoute("article");
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    const routeTarget = event.target.closest("[data-route]");
    if (routeTarget) {
      event.preventDefault();
      setRoute(routeTarget.dataset.route);
      return;
    }

    const articleTarget = event.target.closest("[data-article-id]");
    if (articleTarget) {
      const article = Object.values(articles)
        .flat()
        .find((item) => item.id === articleTarget.dataset.articleId);
      if (article) openArticle(article);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const interactiveCard = event.target.closest(".portal-card, .article-card");
    if (!interactiveCard) return;
    event.preventDefault();
    interactiveCard.click();
  });

  document.querySelectorAll("[data-game-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.gameTab;
      document.querySelectorAll("[data-game-tab]").forEach((item) => {
        item.classList.toggle("subnav-active", item === button);
      });
      document.querySelectorAll("#view-game .article-list").forEach((list) => {
        list.classList.toggle("hidden", list.dataset.category !== tab);
      });
    });
  });

  document.querySelector(".back-button").addEventListener("click", () => {
    setRoute(previousRoute);
  });
}

renderLists();
bindEvents();
setRoute(location.hash.replace("#", "") || "home");
