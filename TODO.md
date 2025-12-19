# TODO - Future Improvements

## High Priority

- [ ] **Add retry logic** - Implement exponential backoff for failed API calls
- [ ] **Job persistence** - Store job metadata in SQLite/PostgreSQL for durability
- [ ] **Authentication** - Add API key or OAuth for job access control
- [ ] **Rate limiting** - Prevent API abuse with request limits

## Medium Priority

- [ ] **Better UI** - Use React/Vue for a more polished interface
- [ ] **Streaming responses** - Stream report generation for real-time updates
- [ ] **More data sources** - Add ArXiv, news APIs, academic databases
- [ ] **Citation formatting** - Proper academic citation styles (APA, MLA)
- [ ] **Job cancellation** - Allow users to cancel running jobs
- [ ] **Job cleanup** - Auto-delete old jobs and files after N days

## Low Priority

- [ ] **Unit tests** - Test individual functions and modules
- [ ] **Integration tests** - Test API endpoints and workflows
- [ ] **E2E tests** - Browser-based testing with Playwright
- [ ] **Logging improvements** - Structured logging with log levels
- [ ] **Metrics/monitoring** - Prometheus metrics, health dashboards
- [ ] **Worker scaling** - Horizontal scaling documentation
- [ ] **PDF enhancements** - Better styling, images, tables
- [ ] **Multi-language** - Support non-English Wikipedia
- [ ] **Caching** - Cache Wikipedia results to reduce API calls
- [ ] **OpenAI function calling** - Full tool calling with model deciding when to call

## Technical Debt

- [ ] **Type hints** - Add comprehensive type annotations
- [ ] **Docstrings** - Expand documentation for all functions
- [ ] **Error codes** - Consistent error response format
- [ ] **Config management** - Centralized configuration with pydantic-settings
- [ ] **Docker optimization** - Multi-stage builds, smaller images

## Ideas for Extension

- [ ] **Voice input** - Accept audio prompts via Whisper
- [ ] **Chart generation** - Create visualizations in reports
- [ ] **Comparison mode** - Compare multiple topics side-by-side
- [ ] **Export formats** - Add DOCX, HTML export options
- [ ] **Scheduled jobs** - Run research on a schedule
- [ ] **Webhooks** - Notify external services when jobs complete

