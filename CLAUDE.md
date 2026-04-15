# Ducati Parts Finder - Project Instructions

## Tools

<smokeDiagnostics>
    <objective>
        Run live smoke tests against marketplace adapters with optional diagnostic capture (screenshots, DOM snapshots) and HTML reporting.
    </objective>
    <command>
        uv run python test_scripts/smoke_test_live.py [OPTIONS]
    </command>
    <info>
        Validates CSS selectors and connectivity against real marketplace sites.
        NOT for CI -- depends on live third-party sites.

        Command line parameters:
        --adapter NAME [NAME...]  Test specific adapters only
        --diagnose               Capture screenshots + DOM for all adapters (auto for EMPTY/ERROR)
        --report                 Generate HTML diagnostic report
        --query "TEXT"           Override default search query (default: "Ducati Multistrada")

        Output:
        - Terminal table: adapter name, status (OK/EMPTY/ERROR/TIMEOUT), result count, time
        - diagnostics/<timestamp>/screenshots/<adapter>.png  (when --diagnose or on failure)
        - diagnostics/<timestamp>/dom/<adapter>.html          (when --diagnose or on failure)
        - diagnostics/<timestamp>/report.html                 (when --report)

        Examples:
        uv run python test_scripts/smoke_test_live.py
        uv run python test_scripts/smoke_test_live.py --adapter bmotor maleducati --diagnose
        uv run python test_scripts/smoke_test_live.py --diagnose --report
        uv run python test_scripts/smoke_test_live.py --query "exhaust pipe" --diagnose --report
    </info>
</smokeDiagnostics>

<selectorTester>
    <objective>
        Test CSS selectors against live marketplace sites for adapter development and debugging.
    </objective>
    <command>
        uv run python test_scripts/selector_tester.py [OPTIONS]
    </command>
    <info>
        Two modes of operation:

        Direct mode: Load a URL and test a CSS selector against it.
        --url URL          URL to load
        --selector SEL     CSS selector to test

        Adapter mode: Run an adapter's full search flow, then test its selectors.
        --adapter NAME     Adapter name from the registry
        --query "TEXT"     Search query (default: "Ducati Multistrada")

        Output:
        - Match count per selector
        - Element previews (tag, classes, text) for first 5 matches
        - Screenshot saved to diagnostics/selector_tests/
        - Selector suggestions when zero matches found

        Examples:
        uv run python test_scripts/selector_tester.py --url https://www.bmotor.hu --selector ".product-item"
        uv run python test_scripts/selector_tester.py --adapter bmotor --query "Multistrada"
        uv run python test_scripts/selector_tester.py --adapter duc_store --query "exhaust"
    </info>
</selectorTester>
