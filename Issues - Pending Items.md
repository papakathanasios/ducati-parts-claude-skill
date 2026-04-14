# Issues - Pending Items

## Pending

### High Priority

1. **Facebook adapter fragility** - Facebook actively blocks automation. The Facebook adapter will require periodic maintenance as selectors and anti-bot measures change. Consider email notification fallback from Facebook Groups.

2. **CSS selector validation** - All Playwright-based adapters have initial CSS selectors that need validation against live sites. Each adapter should be tested manually against its target platform.

3. **OEM part number database expansion** - The seed data covers ~17 parts. The catalog needs expanding with more OEM numbers as the user discovers compatible parts.

### Medium Priority

4. **Currency rate caching** - ECB rates are fetched on every search. Should cache rates for 24 hours to reduce API calls.

5. **Shipping estimate refinement** - Current estimates are rough ranges. Could be improved with actual shipping calculator APIs from major carriers (DHL, DPD, etc.).

### Low Priority

6. **eBay additional image extraction** - Currently only extracts the primary listing image. The Browse API supports fetching additional images.

## Completed

(none yet)
