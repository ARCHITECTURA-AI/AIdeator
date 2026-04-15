(function () {
  function getConfig() {
    return (
      window.__SITE_CONFIG || {
        site: {
          name: "AIdeator",
          tagline:
            "Local-first idea validation with investor-grade, privacy-safe reports."
        },
        cta: {
          primaryLabel: "PyPI",
          primaryHref: "https://pypi.org/project/aideator/",
          contactLabel: "Contact Team",
          contactHref: "/contact/",
          githubHref: "https://github.com/ARCHITECTURA-AI/AIdeator",
          loomHref: "https://www.loom.com/share/REPLACE_WITH_YOUR_VIDEO_ID"
        }
      }
    );
  }

  function getPrefix() {
    var depth = Number(document.body.getAttribute("data-depth") || "0");
    return depth === 0 ? "./" : "../";
  }

  function routeIs(href) {
    var p = window.location.pathname.toLowerCase();
    if (href === "./") {
      return p.endsWith("/") || p.endsWith("/index.html");
    }
    var clean = href.replace("./", "").replace("../", "/").toLowerCase();
    return p.indexOf(clean) !== -1;
  }

  function navLink(prefix, href, label) {
    var active = routeIs(href) ? ' class="active"' : "";
    return '<a' + active + ' href="' + prefix + href + '">' + label + "</a>";
  }

  function mountHeader() {
    var target = document.getElementById("site-header");
    if (!target) return;
    var prefix = getPrefix();
    var config = getConfig();
    var primaryHref = config.cta.primaryHref || "https://pypi.org/project/aideator/";
    target.innerHTML =
      '<header class="site-header">' +
      '<div class="container nav">' +
      '<a class="brand" href="' +
      prefix +
      './"><span class="brand-mark">A</span><span>' +
      config.site.name +
      "</span>" +
      "</a>" +
      '<nav aria-label="Primary">' +
      navLink(prefix, "./features/", "Features") +
      navLink(prefix, "./product/", "Workflow") +
      navLink(prefix, "./pricing/", "Pricing") +
      navLink(prefix, "./docs/", "Docs") +
      navLink(prefix, "./compare/", "Compare") +
      navLink(prefix, "./about/", "About") +
      navLink(prefix, "./blog/", "Blog") +
      navLink(prefix, "./changelog/", "Changelog") +
      "</nav>" +
      '<a class="btn btn-primary" href="' +
      prefix +
      primaryHref +
      '">' +
      config.cta.primaryLabel +
      "</a>" +
      "</div>" +
      "</header>";
  }

  function mountFooter() {
    var target = document.getElementById("site-footer");
    if (!target) return;
    var prefix = getPrefix();
    var config = getConfig();
    var contactSlug = (config.cta.contactHref || "/contact/")
      .replace(/^\/+|\/+$/g, "")
      .replace(/\/+/g, "/");
    var contactPath = prefix + "./" + (contactSlug || "contact") + "/";
    var loom =
      config.cta.loomHref || "https://www.loom.com/share/REPLACE_WITH_YOUR_VIDEO_ID";
    target.innerHTML =
      '<footer class="site-footer">' +
      '<div class="container footer-grid">' +
      "<div>" +
      '<a class="brand" href="' +
      prefix +
      './"><span class="brand-mark">A</span><span>' +
      config.site.name +
      "</span></a>" +
      "<p>" +
      config.site.tagline +
      "</p>" +
      "</div>" +
      "<div>" +
      "<h3>Site</h3>" +
      "<ul>" +
      '<li><a href="' +
      prefix +
      './features/">Features</a></li>' +
      '<li><a href="' +
      prefix +
      './product/">Product</a></li>' +
      '<li><a href="' +
      prefix +
      './pricing/">Pricing</a></li>' +
      '<li><a href="' +
      prefix +
      './docs/">Docs</a></li>' +
      '<li><a href="' +
      prefix +
      './install/">Install</a></li>' +
      '<li><a href="' +
      prefix +
      './compare/">Compare</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      "<h3>Resources</h3>" +
      "<ul>" +
      '<li><a href="https://pypi.org/project/aideator/" target="_blank" rel="noopener">PyPI</a></li>' +
      '<li><a href="https://github.com/ARCHITECTURA-AI/AIdeator" target="_blank" rel="noopener">GitHub</a></li>' +
      '<li><a href="' +
      loom +
      '" target="_blank" rel="noopener">Loom demo</a></li>' +
      '<li><a href="' +
      prefix +
      './changelog/">Changelog</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      "<h3>Company</h3>" +
      "<ul>" +
      '<li><a href="' +
      prefix +
      './about/">About</a></li>' +
      '<li><a href="' +
      prefix +
      './blog/">Blog</a></li>' +
      '<li><a href="' +
      contactPath +
      '">' +
      config.cta.contactLabel +
      "</a></li>" +
      '<li><a href="' +
      prefix +
      './waitlist/">Waitlist</a></li>' +
      '<li><a href="' +
      prefix +
      './signin/">Sign in</a></li>' +
      "</ul>" +
      "</div>" +
      "<div>" +
      "<h3>Legal</h3>" +
      "<ul>" +
      '<li><a href="' +
      prefix +
      './privacy/">Privacy</a></li>' +
      '<li><a href="' +
      prefix +
      './terms/">Terms</a></li>' +
      "</ul>" +
      "</div>" +
      "</div>" +
      "</footer>";
  }

  mountHeader();
  mountFooter();
  document.addEventListener("site-config-loaded", function () {
    mountHeader();
    mountFooter();
  });
})();
