# API-Sports Widgets (v3)

## Usage

- Global config is rendered once near the app root via `ApiSportsConfig`.
- Use `ApiSportsWidget` to render team/player widgets.

### Config example (in App.js)

<api-sports-widget data-type="config"
  data-key="..."
  data-sport="football"
  data-lang="en"
  data-theme="white"
  data-show-errors="true"
  data-show-logos="true"
></api-sports-widget>

### Player full example

<api-sports-widget data-type="player"
  data-player-id="152982"
  data-player-statistics="true"
  data-player-trophies="true"
  data-player-injuries="true"
></api-sports-widget>

### Team examples

- Minimal: data-type="team" data-team-id="39"
- With tab: add data-team-tab="squads"
- With sections: data-team-statistics="true" data-team-squads="true"

### API key

- Place `REACT_APP_APISPORTS_KEY` in a `.env` file to inject the widget key.
- You can also override via localStorage key `APISPORTS_WIDGET_KEY` or URL `?apisportsKey=...` during development.
