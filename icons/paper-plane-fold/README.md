# Paper plane fold icons

Six minimal line icons that take a sheet of paper through to a finished plane.

| Step | Icon | What it shows |
| --- | --- | --- |
| 1 | <img src="step-1-sheet.svg" width="28" alt="" /> | Blank sheet with the first corner crease |
| 2 | <img src="step-2-first-corner.svg" width="28" alt="" /> | One corner folded to the centre line |
| 3 | <img src="step-3-nose.svg" width="28" alt="" /> | Both corners folded into a nose |
| 4 | <img src="step-4-half-fold.svg" width="28" alt="" /> | Folded in half along the spine |
| 5 | <img src="step-5-wing.svg" width="28" alt="" /> | Both wings folded out |
| 6 | <img src="step-6-plane.svg" width="28" alt="" /> | Ready to fly |

Open [`index.html`](index.html) for a preview of all six at several sizes and tints.

## Design

- 24 x 24 viewBox on a 3px padding grid, so they line up with Lucide / Feather sets.
- `1.5` stroke, round caps and joins, no fills.
- Solid strokes are paper edges and folds already made; dashed strokes at `0.55` opacity are the
  next crease to fold.
- Light orange `#FFA45C` by default.

## Usage

Each icon strokes with `currentColor` and carries the default orange as an inline `color` style, so
dropping the file straight into an `<img>` gives the light orange version:

```html
<img src="icons/paper-plane-fold/step-6-plane.svg" width="24" height="24" alt="Paper plane" />
```

To recolour, inline the SVG (or reference the sprite) and set `color` on the element:

```html
<svg width="24" height="24"><use href="paper-plane-fold.sprite.svg#ppf-step-6" /></svg>
```

```css
svg {
  color: #f2762b;
}
```

`paper-plane-fold.sprite.svg` holds all six as `<symbol>` elements with the ids `ppf-step-1`
through `ppf-step-6`.
