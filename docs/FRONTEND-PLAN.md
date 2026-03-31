Below is a **comprehensive HTML + Jinja plan** for the app (excluding marketing landing). Treat this as a blueprint for templates, includes, and which views hit which endpoints.

I’ll assume:

- Python backend (FastAPI/Flask-style)  
- Jinja2 templates in `templates/`  
- Static assets in `static/`

***

## 1. Template layout structure

### 1.1 Base layout

`templates/base.html`

- Purpose: global shell, loaded on every app page.
- Blocks:
  - `{% block head_extra %}{% endblock %}`
  - `{% block topbar_extra %}{% endblock %}`
  - `{% block sidebar_extra %}{% endblock %}`
  - `{% block content %}{% endblock %}`
  - `{% block scripts %}{% endblock %}`

**Skeleton**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{% block title %}AIdeator{% endblock %}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="{{ url_for('static', filename='css/app.css') }}" rel="stylesheet">
  {% block head_extra %}{% endblock %}
</head>
<body class="app-bg">
  {% include "partials/topbar.html" %}
  <div class="app-shell">
    {% include "partials/sidebar.html" %}
    <main class="app-main">
      {% block content %}{% endblock %}
    </main>
  </div>
  <script src="{{ url_for('static', filename='js/app.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

***

### 1.2 Shared partials

- `templates/partials/topbar.html`
- `templates/partials/sidebar.html`
- `templates/partials/flash.html` (alerts/toasts)
- `templates/partials/pagination.html`
- `templates/partials/status-pill.html` (run status)
- `templates/partials/mode-pill.html` (local/hybrid/cloud)
- `templates/partials/empty-state.html`

You’ll use these across pages.

***

## 2. Dashboard

### Template

`templates/dashboard.html`

Extends `base.html`.

**Context data from view (Python)**

- `summary_ideas_count`
- `summary_runs_last_24h`
- `summary_runs_failed_last_24h`
- `recent_ideas` (list of `{id, title, created_at, runs_count, last_run_status}`)
- `recent_runs` (list of `{id, idea_title, status, mode, tier, started_at}`)
- `current_mode` (`"local"|"hybrid"|"cloud"`)

**View hits endpoints**

In Python view:

- `GET /ideas?limit=5`
- `GET /runs?limit=5&order=desc`
- `GET /settings`

**HTML + Jinja skeleton**

```html
{% extends "base.html" %}
{% block title %}Dashboard · AIdeator{% endblock %}

{% block content %}
  {% include "partials/flash.html" %}
  <section class="section">
    <div class="grid-3">
      <div class="card metric">
        <h2>Ideas</h2>
        <p class="metric-number">{{ summary_ideas_count }}</p>
        <a href="{{ url_for('ideas_list') }}" class="link">View all ideas</a>
      </div>
      <div class="card metric">
        <h2>Runs (24h)</h2>
        <p class="metric-number">{{ summary_runs_last_24h }}</p>
        <p class="metric-sub">Failed: {{ summary_runs_failed_last_24h }}</p>
      </div>
      <div class="card metric">
        <h2>Default mode</h2>
        {% include "partials/mode-pill.html" with context %}
        <a href="{{ url_for('settings_modes') }}" class="link">Manage modes</a>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-header">
      <h2>Recent ideas</h2>
      <a href="{{ url_for('ideas_list') }}" class="btn secondary">View all</a>
    </div>
    {% if recent_ideas %}
      <table class="table">
        <thead>
          <tr>
            <th>Idea</th>
            <th>Created</th>
            <th>Runs</th>
            <th>Last run</th>
          </tr>
        </thead>
        <tbody>
          {% for idea in recent_ideas %}
          <tr>
            <td>
              <a href="{{ url_for('idea_detail', idea_id=idea.id) }}">{{ idea.title }}</a>
            </td>
            <td>{{ idea.created_at }}</td>
            <td>{{ idea.runs_count }}</td>
            <td>{% include "partials/status-pill.html" with status=idea.last_run_status %}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      {% include "partials/empty-state.html" with
         message="No ideas yet."
         cta_url=url_for('ideas_new')
         cta_label="Create your first idea"
      %}
    {% endif %}
  </section>

  <section class="section">
    <div class="section-header">
      <h2>Recent runs</h2>
      <a href="{{ url_for('runs_list') }}" class="btn secondary">View all</a>
    </div>
    {% if recent_runs %}
      <table class="table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Idea</th>
            <th>Status</th>
            <th>Mode</th>
            <th>Started</th>
          </tr>
        </thead>
        <tbody>
          {% for run in recent_runs %}
          <tr>
            <td>
              <a href="{{ url_for('run_detail', run_id=run.id) }}">#{{ run.id }}</a>
            </td>
            <td>{{ run.idea_title }}</td>
            <td>{% include "partials/status-pill.html" with status=run.status %}</td>
            <td>{% include "partials/mode-pill.html" with mode=run.mode %}</td>
            <td>{{ run.started_at }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      {% include "partials/empty-state.html" with
         message="No runs yet."
         cta_url=url_for('ideas_list')
         cta_label="Create a run"
      %}
    {% endif %}
  </section>
{% endblock %}
```

***

## 3. Ideas – List

### Template

`templates/ideas/list.html`

**Context**

- `ideas` (paginated list)
- `pagination` (page, pages, has_next, has_prev)
- `query` (search string)

**View endpoints**

- `GET /ideas?query=&page=&per_page=`

**HTML + Jinja**

```html
{% extends "base.html" %}
{% block title %}Ideas · AIdeator{% endblock %}

{% block content %}
  {% include "partials/flash.html" %}

  <section class="section">
    <div class="section-header">
      <h1>Ideas</h1>
      <a href="{{ url_for('ideas_new') }}" class="btn primary">New idea</a>
    </div>

    <form method="get" class="form-inline">
      <input type="text" name="q" placeholder="Search ideas"
             value="{{ query or '' }}" class="input">
      <button class="btn secondary" type="submit">Search</button>
    </form>

    {% if ideas %}
      <table class="table">
        <thead>
          <tr>
            <th>Idea</th>
            <th>Created</th>
            <th>Runs</th>
            <th>Last run</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {% for idea in ideas %}
          <tr>
            <td>
              <a href="{{ url_for('idea_detail', idea_id=idea.id) }}">{{ idea.title }}</a>
            </td>
            <td>{{ idea.created_at }}</td>
            <td>{{ idea.runs_count }}</td>
            <td>{% include "partials/status-pill.html" with status=idea.last_run_status %}</td>
            <td class="table-actions">
              <a href="{{ url_for('idea_detail', idea_id=idea.id) }}" class="btn ghost">Open</a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>

      {% include "partials/pagination.html" with pagination=pagination %}
    {% else %}
      {% include "partials/empty-state.html" with
         message="No ideas found."
         cta_url=url_for('ideas_new')
         cta_label="Create idea"
      %}
    {% endif %}
  </section>
{% endblock %}
```

***

### Idea – New (can be separate or modal)

`templates/ideas/new.html`

- Form fields: title, description, tags (optional).
- On submit: POST to `/ideas`, then redirect to Idea Detail or Ideas List.

***

## 4. Idea – Detail

`templates/ideas/detail.html`

**Context**

- `idea` (full object)
- `runs` (list for this idea)
- `default_mode`, `available_modes`

**View endpoints**

- `GET /ideas/{idea_id}`
- `GET /runs?idea_id={idea_id}`

**Run creation endpoint**

- `POST /runs` from form on this page.

**HTML + Jinja**

```html
{% extends "base.html" %}
{% block title %}{{ idea.title }} · AIdeator{% endblock %}

{% block content %}
  {% include "partials/flash.html" %}

  <section class="section">
    <header class="detail-header">
      <div>
        <h1>{{ idea.title }}</h1>
        <p class="meta">Created {{ idea.created_at }}</p>
      </div>
      <div>
        <a href="{{ url_for('docs_for_idea', idea_id=idea.id) }}" class="btn secondary">
          View report docs
        </a>
      </div>
    </header>

    <div class="grid-2">
      <article class="card">
        <h2>Description</h2>
        <p class="body">{{ idea.description }}</p>
      </article>

      <article class="card">
        <h2>New run</h2>
        <form method="post" action="{{ url_for('runs_create') }}">
          <input type="hidden" name="idea_id" value="{{ idea.id }}">
          <label class="label">Mode</label>
          <select name="mode" class="input">
            {% for mode in available_modes %}
            <option value="{{ mode.value }}"
                    {% if mode.value == default_mode %}selected{% endif %}>
              {{ mode.label }}
            </option>
            {% endfor %}
          </select>

          <label class="label">Tier</label>
          <select name="tier" class="input">
            <option value="baseline">Baseline</option>
            <option value="richer">Richer</option>
          </select>

          <button type="submit" class="btn primary">Run validation</button>
        </form>
      </article>
    </div>
  </section>

  <section class="section">
    <h2>Run history</h2>
    {% if runs %}
      <table class="table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Status</th>
            <th>Mode</th>
            <th>Tier</th>
            <th>Started</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {% for run in runs %}
          <tr>
            <td>
              <a href="{{ url_for('run_detail', run_id=run.id) }}">#{{ run.id }}</a>
            </td>
            <td>{% include "partials/status-pill.html" with status=run.status %}</td>
            <td>{% include "partials/mode-pill.html" with mode=run.mode %}</td>
            <td>{{ run.tier }}</td>
            <td>{{ run.started_at }}</td>
            <td>{{ run.duration or '—' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      {% include "partials/empty-state.html" with
         message="No runs yet for this idea."
         cta_url=url_for('runs_create_for_idea', idea_id=idea.id)
         cta_label="Run first validation"
      %}
    {% endif %}
  </section>
{% endblock %}
```

***

## 5. Runs – List

`templates/runs/list.html`

**Context**

- `runs` (paginated)
- `filters` (status, mode)
- `pagination`

**Endpoints**

- `GET /runs?status=&mode=&page=`

**HTML + Jinja**

```html
{% extends "base.html" %}
{% block title %}Runs · AIdeator{% endblock %}

{% block content %}
  {% include "partials/flash.html" %}

  <section class="section">
    <div class="section-header">
      <h1>Runs</h1>
    </div>

    <form method="get" class="form-inline">
      <select name="status" class="input">
        <option value="">All statuses</option>
        {% for s in ["pending","running","succeeded","failed"] %}
        <option value="{{ s }}" {% if filters.status == s %}selected{% endif %}>
          {{ s|capitalize }}
        </option>
        {% endfor %}
      </select>
      <select name="mode" class="input">
        <option value="">All modes</option>
        {% for m in ["local","hybrid","cloud"] %}
        <option value="{{ m }}" {% if filters.mode == m %}selected{% endif %}>
          {{ m|capitalize }}
        </option>
        {% endfor %}
      </select>
      <button class="btn secondary" type="submit">Filter</button>
    </form>

    {% if runs %}
      <table class="table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Idea</th>
            <th>Status</th>
            <th>Mode</th>
            <th>Tier</th>
            <th>Started</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {% for run in runs %}
          <tr>
            <td><a href="{{ url_for('run_detail', run_id=run.id) }}">#{{ run.id }}</a></td>
            <td>{{ run.idea_title }}</td>
            <td>{% include "partials/status-pill.html" with status=run.status %}</td>
            <td>{% include "partials/mode-pill.html" with mode=run.mode %}</td>
            <td>{{ run.tier }}</td>
            <td>{{ run.started_at }}</td>
            <td>{{ run.duration or '—' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>

      {% include "partials/pagination.html" with pagination=pagination %}
    {% else %}
      {% include "partials/empty-state.html" with
         message="No runs yet."
         cta_url=url_for('ideas_list')
         cta_label="Create a run"
      %}
    {% endif %}
  </section>
{% endblock %}
```

***

## 6. Run – Detail

`templates/runs/detail.html`

**Context**

- `run` (id, idea_id, idea_title, status, mode, tier, timestamps, duration, error_code, error_message)
- `cards` (Demand, Competition, Risk, Next Steps)
- `signals` (optional list; or view separated into tab)
- `docs_available` (boolean)
- `docs_url` (if available)

**Endpoints in view**

- `GET /runs/{run_id}/status`
- `GET /runs/{run_id}/report`
- `GET /runs/{run_id}/signals`

**HTML + Jinja**

```html
{% extends "base.html" %}
{% block title %}Run #{{ run.id }} · AIdeator{% endblock %}

{% block content %}
  {% include "partials/flash.html" %}

  <section class="section">
    <header class="detail-header">
      <div>
        <h1>Run #{{ run.id }}</h1>
        <p class="meta">
          Idea:
          <a href="{{ url_for('idea_detail', idea_id=run.idea_id) }}">{{ run.idea_title }}</a>
        </p>
      </div>
      <div class="detail-status">
        {% include "partials/status-pill.html" with status=run.status %}
        {% include "partials/mode-pill.html" with mode=run.mode %}
        <span class="tag">{{ run.tier|capitalize }}</span>
      </div>
    </header>

    {% if run.status == "failed" %}
      <div class="alert error">
        <strong>Run failed.</strong>
        {% if run.error_code %}
          <div>Code: {{ run.error_code }}</div>
        {% endif %}
        {% if run.error_message %}
          <div>{{ run.error_message }}</div>
        {% endif %}
      </div>
    {% endif %}

    <div class="grid-2">
      <article class="card">
        <h2>Timeline</h2>
        <ul class="timeline">
          <li>Queued: {{ run.queued_at or "—" }}</li>
          <li>Started: {{ run.started_at or "—" }}</li>
          <li>Finished: {{ run.finished_at or "—" }}</li>
          <li>Duration: {{ run.duration or "—" }}</li>
        </ul>
      </article>

      <article class="card">
        <h2>Output</h2>
        <p>Summary of this run’s main outcomes.</p>
        {% if docs_available %}
          <a href="{{ docs_url }}" class="btn secondary">Open markdown report</a>
        {% endif %}
      </article>
    </div>
  </section>

  <section class="section">
    <h2>Report cards</h2>
    {% if cards %}
      <div class="grid-4">
        {% for card in cards %}
        <article class="card report-card">
          <header class="card-header">
            <h3>{{ card.title }}</h3>
            <span class="score">{{ card.score }}</span>
          </header>
          <p class="body">{{ card.summary }}</p>
          {% if card.citations %}
            <button class="link" type="button" data-toggle="card-citations-{{ loop.index }}">
              View citations
            </button>
            <ul id="card-citations-{{ loop.index }}" class="citations" hidden>
              {% for c in card.citations %}
              <li>{{ c }}</li>
              {% endfor %}
            </ul>
          {% endif %}
        </article>
        {% endfor %}
      </div>
    {% else %}
      <p>No report cards available yet.</p>
    {% endif %}
  </section>

  <section class="section">
    <h2>Signals</h2>
    {% if signals %}
      <table class="table">
        <thead>
          <tr>
            <th>Source</th>
            <th>Title</th>
            <th>Snippet</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {% for sig in signals %}
          <tr>
            <td>{{ sig.source }}</td>
            <td>{{ sig.title }}</td>
            <td>{{ sig.snippet }}</td>
            <td>
              {% if sig.url %}
              <a href="{{ sig.url }}" target="_blank" rel="noopener">Open</a>
              {% else %}
              —
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No signals recorded for this run.</p>
    {% endif %}
  </section>
{% endblock %}
```

***

## 7. Docs / Reports Browser

`templates/docs/browser.html`

**Context**

- `docs` (list of `{idea_id, idea_title, updated_at}`)
- `selected_doc` (markdown rendered as safe HTML)
- `selected_idea_id`

**Endpoints**

- `GET /docs`
- `GET /docs/{idea_id}`

**HTML + Jinja**

```html
{% extends "base.html" %}
{% block title %}Reports · AIdeator{% endblock %}

{% block content %}
  <section class="section docs-shell">
    <aside class="docs-list">
      <h1>Reports</h1>
      <ul>
        {% for doc in docs %}
        <li class="{% if doc.idea_id == selected_idea_id %}is-active{% endif %}">
          <a href="{{ url_for('docs_for_idea', idea_id=doc.idea_id) }}">
            {{ doc.idea_title }}
            <span class="meta">{{ doc.updated_at }}</span>
          </a>
        </li>
        {% endfor %}
      </ul>
    </aside>

    <article class="docs-viewer">
      {% if selected_doc %}
        {{ selected_doc|safe }}
      {% else %}
        <p>Select a report from the left.</p>
      {% endif %}
    </article>
  </section>
{% endblock %}
```

***

## 8. Settings

You can have separate templates or a single tabbed page.

### Settings – Modes & Privacy

`templates/settings/modes.html`

**Context**

- `settings` object with mode default, descriptions, flags.

**Endpoints**

- `GET /settings`
- `POST/PUT /settings` for mode fields.

### Settings – Integrations

`templates/settings/integrations.html`

**Context**

- `settings.integrations` (keys, status)

**Endpoints**

- `GET /settings`
- `PUT /settings` (integrations)
- `POST /settings/test-integration`

### Settings – System

`templates/settings/system.html`

**Context**

- DB path, docs path, concurrency, etc.

**Endpoints**

- `GET /settings`
- `PUT /settings` (some fields)

***

## 9. Admin / Diagnostics

`templates/admin/diagnostics.html`

**Context**

- `health` (status)
- `diagnostics` (queue size, last errors)

**Endpoints**

- `GET /health`
- `GET /diagnostics`

***

## 10. Shared partials and components

### 10.1 Topbar

`partials/topbar.html`

- Uses `current_user`, `current_route`, `current_mode`.

### 10.2 Sidebar

`partials/sidebar.html`

- Nav items use `url_for()` and compare to `request.endpoint` for active state.

### 10.3 Status pill

`partials/status-pill.html`

```html
{% macro status_pill(status) %}
  <span class="status-pill status-{{ status }}">
    {{ status|capitalize }}
  </span>
{% endmacro %}

{{ status_pill(status) }}
```

### 10.4 Mode pill

`partials/mode-pill.html`

```html
{% macro mode_pill(mode) %}
  <span class="mode-pill mode-{{ mode }}">
    {{ mode|replace("_"," ")|capitalize }}
  </span>
{% endmacro %}

{{ mode_pill(mode or current_mode) }}
```

### 10.5 Empty state

`partials/empty-state.html`

```html
<div class="empty-state">
  <p>{{ message }}</p>
  {% if cta_url and cta_label %}
    <a href="{{ cta_url }}" class="btn primary">{{ cta_label }}</a>
  {% endif %}
</div>
```

***

## 11. Connecting everything (backend glue)

For each template:

- Define a view function/route in Python.
- In the view:
  - Call your **internal service or HTTP client** for the corresponding endpoint (`GET /ideas`, etc.).
  - Transform response JSON into context dictionaries/lists.
  - Render the appropriate template.

Example (Flask-style):

```python
@app.get("/dashboard")
def dashboard():
    ideas = api.get_ideas(limit=5)
    runs = api.get_runs(limit=5, order="desc")
    settings = api.get_settings()

    return render_template(
        "dashboard.html",
        summary_ideas_count=ideas["total"],
        summary_runs_last_24h=runs["last_24h_count"],
        summary_runs_failed_last_24h=runs["last_24h_failed"],
        recent_ideas=ideas["items"],
        recent_runs=runs["items"],
        current_mode=settings["default_mode"],
    )
```

You can repeat this pattern for each page.

***
