(function () {
  function getPrefix() {
    var depth = Number(document.body.getAttribute("data-depth") || "0");
    return depth === 0 ? "./" : "../";
  }

  function normalizePath(pathname) {
    if (!pathname || pathname === "/") return "/";
    if (pathname.endsWith(".html")) {
      return pathname.replace("index.html", "");
    }
    return pathname.endsWith("/") ? pathname : pathname + "/";
  }

  function setMeta(name, value, isProperty) {
    var query = isProperty
      ? 'meta[property="' + name + '"]'
      : 'meta[name="' + name + '"]';
    var el = document.querySelector(query);
    if (!el) {
      el = document.createElement("meta");
      if (isProperty) {
        el.setAttribute("property", name);
      } else {
        el.setAttribute("name", name);
      }
      document.head.appendChild(el);
    }
    el.setAttribute("content", value);
  }

  function applySeo(config) {
    var route = normalizePath(window.location.pathname.toLowerCase());
    var seo = config.seo[route];
    if (!seo) return;
    var routeKey = route === "/" ? "home" : route.replaceAll("/", "");
    var siteBaseUrl = (config.site && config.site.baseUrl) || "https://aideator.app";

    if (seo.title) document.title = seo.title;
    if (seo.description) setMeta("description", seo.description, false);
    if (seo.canonical) {
      var canonical = document.querySelector('link[rel="canonical"]');
      if (canonical) canonical.setAttribute("href", seo.canonical);
      setMeta("og:url", seo.canonical, true);
    }
    if (seo.title) {
      setMeta("og:title", seo.title, true);
      setMeta("twitter:title", seo.title, false);
    }
    if (seo.description) {
      setMeta("og:description", seo.description, true);
      setMeta("twitter:description", seo.description, false);
    }
    setMeta("twitter:card", "summary_large_image", false);
    setMeta(
      "og:image",
      siteBaseUrl + "/og/" + routeKey + ".png",
      true
    );
    setMeta(
      "twitter:image",
      siteBaseUrl + "/og/" + routeKey + ".png",
      false
    );
  }

  function upsertJsonLdScript(id, obj) {
    var existing = document.getElementById(id);
    var script = existing || document.createElement("script");
    script.type = "application/ld+json";
    script.id = id;
    script.textContent = JSON.stringify(obj);
    if (!existing) document.head.appendChild(script);
  }

  function titleFromSlug(slug) {
    if (!slug) return "Home";
    return slug
      .split("-")
      .map(function (part) {
        return part.charAt(0).toUpperCase() + part.slice(1);
      })
      .join(" ");
  }

  function applyBreadcrumbJsonLd(config) {
    var pathname = normalizePath(window.location.pathname.toLowerCase());
    if (pathname === "/") return;
    var baseUrl = (config.site && config.site.baseUrl) || "https://aideator.app";
    var siteName = (config.site && config.site.name) || "AIdeator";
    var parts = pathname.split("/").filter(Boolean);

    var itemList = [
      {
        "@type": "ListItem",
        position: 1,
        name: "Home",
        item: baseUrl + "/"
      }
    ];

    var running = "";
    parts.forEach(function (part, idx) {
      running += "/" + part;
      itemList.push({
        "@type": "ListItem",
        position: idx + 2,
        name: part === siteName ? siteName : titleFromSlug(part),
        item: baseUrl + running + "/"
      });
    });

    upsertJsonLdScript("breadcrumb-jsonld", {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: itemList
    });
  }

  function applyBindings(config) {
    var siteNameNodes = document.querySelectorAll('[data-config="site.name"]');
    siteNameNodes.forEach(function (el) {
      el.textContent = config.site.name;
    });

    var taglineNodes = document.querySelectorAll('[data-config="site.tagline"]');
    taglineNodes.forEach(function (el) {
      el.textContent = config.site.tagline;
    });
  }

  function loadConfig() {
    var prefix = getPrefix();
    fetch(prefix + "site.config.json")
      .then(function (response) {
        return response.json();
      })
      .then(function (config) {
        window.__SITE_CONFIG = config;
        applySeo(config);
        applyBindings(config);
        applyBreadcrumbJsonLd(config);
        document.dispatchEvent(new CustomEvent("site-config-loaded"));
      })
      .catch(function () {
        // Non-fatal fallback: static page values remain in place.
      });
  }

  loadConfig();
})();
