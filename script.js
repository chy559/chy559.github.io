const state = {
  articlesByCategory: {
    tech: [],
    galgame: [],
    nongalgame: []
  },
  articlesBySlug: new Map(),
  featured: null,
  previousRoute: "home",
  currentGameTab: "galgame"
};

const placeholders = {
  tech: {
    title: "技术文章还在整理中",
    text: "之后这里会放前端、工程化、项目复盘和学习笔记。"
  },
  galgame: {
    title: "Galgame 记录还在整理中",
    text: "这里会收纳视觉小说感想、路线记录和推荐。"
  },
  nongalgame: {
    title: "非 Galgame 记录还在整理中",
    text: "这里会放动作、RPG、独立游戏以及其他游玩碎片。"
  }
};

function escapeHtml(value = "") {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function slugToCategoryLabel(category) {
  switch (category) {
    case "tech":
      return "Tech";
    case "galgame":
      return "Galgame";
    case "nongalgame":
      return "Non-Galgame";
    default:
      return category;
  }
}

function formatDate(value) {
  if (!value) return "未标注日期";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric"
  }).format(date);
}

function estimateReadingTime(wordCount) {
  const count = Number(wordCount) || 0;
  const minutes = Math.max(1, Math.round(count / 280));
  return `${minutes} min read`;
}

function stripFrontmatter(rawMarkdown) {
  if (!rawMarkdown.startsWith("---\n")) return rawMarkdown;
  const endMarker = "\n---\n";
  const endIndex = rawMarkdown.indexOf(endMarker, 4);
  if (endIndex === -1) return rawMarkdown;
  return rawMarkdown.slice(endIndex + endMarker.length).trim();
}

function inlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" loading="lazy" />')
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let paragraph = [];
  let listItems = [];
  let blockquote = [];
  let codeLines = [];
  let codeLang = "";
  let inCodeBlock = false;

  function flushParagraph() {
    if (!paragraph.length) return;
    blocks.push(`<p>${inlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  }

  function flushList() {
    if (!listItems.length) return;
    blocks.push(`<ul>${listItems.map((item) => `<li>${inlineMarkdown(item)}</li>`).join("")}</ul>`);
    listItems = [];
  }

  function flushQuote() {
    if (!blockquote.length) return;
    blocks.push(`<blockquote><p>${inlineMarkdown(blockquote.join(" "))}</p></blockquote>`);
    blockquote = [];
  }

  function flushCode() {
    if (!codeLines.length && !inCodeBlock) return;
    const langClass = codeLang ? ` class="language-${escapeHtml(codeLang)}"` : "";
    blocks.push(
      `<pre><code${langClass}>${escapeHtml(codeLines.join("\n"))}</code></pre>`
    );
    codeLines = [];
    codeLang = "";
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith("```")) {
      flushParagraph();
      flushList();
      flushQuote();

      if (!inCodeBlock) {
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
      } else {
        inCodeBlock = false;
        flushCode();
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(rawLine);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      flushQuote();
      continue;
    }

    if (/^!\[[^\]]*\]\([^)]+\)$/.test(line.trim())) {
      flushParagraph();
      flushList();
      flushQuote();
      blocks.push(`<figure class="article-media">${inlineMarkdown(line.trim())}</figure>`);
      continue;
    }

    if (/^#{1,3}\s/.test(line)) {
      flushParagraph();
      flushList();
      flushQuote();
      const level = line.match(/^#+/)[0].length;
      blocks.push(`<h${level + 1}>${inlineMarkdown(line.replace(/^#{1,3}\s/, ""))}</h${level + 1}>`);
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      flushParagraph();
      flushQuote();
      listItems.push(line.replace(/^[-*]\s+/, ""));
      continue;
    }

    if (/^>\s?/.test(line)) {
      flushParagraph();
      flushList();
      blockquote.push(line.replace(/^>\s?/, ""));
      continue;
    }

    paragraph.push(line.trim());
  }

  flushParagraph();
  flushList();
  flushQuote();
  flushCode();

  return blocks.join("");
}

async function fetchText(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.text();
}

function renderFeatured() {
  const slot = document.querySelector("#featured-article");
  if (!slot) return;

  const featured = state.featured;
  if (!featured) {
    slot.classList.remove("skeleton-block");
    slot.innerHTML = `
      <article class="featured-card empty-state">
        <p class="eyebrow">Archive status</p>
        <h3>第一篇文章还没放进来</h3>
        <p>等你把 markdown 文章放进内容目录，这里会自动显示最近更新。</p>
      </article>
    `;
    return;
  }

  slot.classList.remove("skeleton-block");
  slot.innerHTML = `
    <article class="featured-card" data-article-slug="${featured.slug}" tabindex="0">
      <div class="featured-meta">
        <span class="meta-chip">${slugToCategoryLabel(featured.category)}</span>
        <span class="meta-chip">${formatDate(featured.date)}</span>
      </div>
      <h3>${escapeHtml(featured.title)}</h3>
      <p>${escapeHtml(featured.summary)}</p>
      <span class="featured-link">阅读全文</span>
    </article>
  `;
}

function renderLists() {
  document.querySelectorAll(".article-list").forEach((list) => {
    const category = list.dataset.category;
    const items = state.articlesByCategory[category] || [];

    if (!items.length) {
      const empty = placeholders[category];
      list.innerHTML = `
        <article class="empty-state">
          <p class="eyebrow">${slugToCategoryLabel(category)}</p>
          <h2>${escapeHtml(empty.title)}</h2>
          <p>${escapeHtml(empty.text)}</p>
        </article>
      `;
      return;
    }

    list.innerHTML = items
      .map(
        (article) => `
          <article class="article-card" tabindex="0" data-article-slug="${article.slug}">
            <div class="article-card-main">
              <div class="article-card-meta">
                <span class="article-tag">${slugToCategoryLabel(article.category)}</span>
                <span>${formatDate(article.date)}</span>
              </div>
              <h2>${escapeHtml(article.title)}</h2>
              <p>${escapeHtml(article.summary)}</p>
            </div>
            <span class="article-card-tail">
              <span>${escapeHtml(article.readingTime)}</span>
              <span class="tail-arrow" aria-hidden="true">→</span>
            </span>
          </article>
        `
      )
      .join("");
  });
}

function setRoute(route, options = {}) {
  const normalized = route || "home";
  const target = document.querySelector(`#view-${normalized}`);
  if (!target) return;

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("view-active", view === target);
  });

  document.querySelectorAll(".main-nav [data-route], .brand[data-route]").forEach((link) => {
    link.classList.toggle("nav-active", link.dataset.route === normalized);
  });

  if (normalized !== "article") {
    state.previousRoute = normalized;
  }

  if (!options.skipHistory) {
    if (normalized === "article" && options.slug) {
      window.history.replaceState(null, "", `#article/${options.slug}`);
    } else {
      window.history.replaceState(null, "", `#${normalized}`);
    }
  }

  window.scrollTo({ top: 0, behavior: options.instant ? "auto" : "smooth" });
}

async function openArticleBySlug(slug) {
  const article = state.articlesBySlug.get(slug);
  if (!article) return;

  const contentNode = document.querySelector("#detail-content");
  document.querySelector("#detail-category").textContent = slugToCategoryLabel(article.category);
  document.querySelector("#detail-title").textContent = article.title;
  document.querySelector("#detail-summary").textContent = article.summary;
  document.querySelector("#detail-date").textContent = formatDate(article.date);
  document.querySelector("#detail-reading").textContent = article.readingTime;
  contentNode.classList.add("skeleton-block");
  contentNode.innerHTML = "";

  setRoute("article", { slug });

  try {
    const markdown = article.content || stripFrontmatter(await fetchText(article.path));
    contentNode.innerHTML = renderMarkdown(markdown);
  } catch (error) {
    console.error("Article render failed", {
      slug,
      path: article.path,
      hasEmbeddedContent: Boolean(article.content),
      error
    });
    contentNode.innerHTML = `
      <div class="empty-state">
        <h2>正文加载失败</h2>
        <p>这篇文章的正文没有从内容索引中读到，单篇 markdown 备用加载也失败了。请确认 GitHub Pages 已部署最新的 posts-manifest.json 和 script.js。</p>
      </div>
    `;
  } finally {
    contentNode.classList.remove("skeleton-block");
  }
}

function parseHash() {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return { route: "home" };
  if (hash.startsWith("article/")) {
    return { route: "article", slug: hash.slice("article/".length) };
  }
  return { route: hash };
}

function setupData(posts) {
  const sorted = [...posts].sort((a, b) => new Date(b.date) - new Date(a.date));

  state.articlesByCategory = {
    tech: sorted.filter((post) => post.category === "tech"),
    galgame: sorted.filter((post) => post.category === "galgame"),
    nongalgame: sorted.filter((post) => post.category === "nongalgame")
  };
  state.articlesBySlug = new Map(sorted.map((post) => [post.slug, post]));
  state.featured = sorted[0] || null;
}

async function loadPosts() {
  const manifestText = await fetchText("./content/posts-manifest.json");
  const posts = JSON.parse(manifestText).posts || [];

  setupData(
    posts.map((post) => ({
      ...post,
      readingTime: estimateReadingTime(post.wordCount)
    }))
  );
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    const routeTarget = event.target.closest("[data-route]");
    if (routeTarget) {
      event.preventDefault();
      setRoute(routeTarget.dataset.route);
      return;
    }

    const articleTarget = event.target.closest("[data-article-slug]");
    if (articleTarget) {
      openArticleBySlug(articleTarget.dataset.articleSlug);
      return;
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const interactiveCard = event.target.closest(".category-tile, .article-card, .featured-card");
    if (!interactiveCard) return;
    event.preventDefault();
    interactiveCard.click();
  });

  document.querySelectorAll("[data-game-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.gameTab;
      state.currentGameTab = tab;

      document.querySelectorAll("[data-game-tab]").forEach((item) => {
        item.classList.toggle("subnav-active", item === button);
      });

      document.querySelectorAll("#view-game .article-list").forEach((list) => {
        list.classList.toggle("hidden", list.dataset.category !== tab);
      });
    });
  });

  document.querySelector(".back-button").addEventListener("click", () => {
    setRoute(state.previousRoute);
  });

  window.addEventListener("hashchange", () => {
    const parsed = parseHash();
    if (parsed.route === "article" && parsed.slug) {
      openArticleBySlug(parsed.slug);
      return;
    }
    setRoute(parsed.route, { skipHistory: true, instant: true });
  });
}

async function init() {
  bindEvents();

  try {
    await loadPosts();
    renderFeatured();
    renderLists();
  } catch (error) {
    document.querySelectorAll(".article-list").forEach((list) => {
      list.innerHTML = `
        <article class="empty-state">
          <h2>内容索引加载失败</h2>
          <p>请确认通过本地服务器打开项目，并且 content/posts-manifest.json 已成功生成。</p>
        </article>
      `;
    });
    renderFeatured();
  }

  const parsed = parseHash();
  if (parsed.route === "article" && parsed.slug) {
    await openArticleBySlug(parsed.slug);
    return;
  }

  setRoute(parsed.route, { skipHistory: true, instant: true });
}

init();
