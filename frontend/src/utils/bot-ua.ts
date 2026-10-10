/**
 * Client-side crawler / lab-run detection — the same list as the server
 * `isBot()` (src/utils/is-bot.ts) and the root layout's head script, read
 * from `navigator.userAgent` so the page stays statically prerendered (a
 * `headers()` read on the route would opt it out).
 *
 * Only ever gates decoration a crawler has no use for: the preloader and the
 * WebGL particle stream. Content is the same for everyone.
 *
 * AI crawlers (GPTBot, ClaudeBot, PerplexityBot, …) run no JavaScript: they get
 * the robot form too, or streamed copy reads to them as `hidden` (2026-10-02).
 */
export const BOT_UA =
  /lighthouse|googlebot|pagespeed|headlesschrome|gtmetrix|pingdom|bingbot|yandexbot|gptbot|chatgpt-user|oai-searchbot|claudebot|claude-user|claude-searchbot|anthropic-ai|perplexitybot|perplexity-user|ccbot|bytespider|amazonbot|meta-externalagent|cohere-ai|mistralai-user|youbot|diffbot/i;

export const isBotClient = () =>
  typeof navigator !== "undefined" && BOT_UA.test(navigator.userAgent);

/** The same list, read from a request's UA — the robot proxy (D-016). */
export const isBotUserAgent = (userAgent: string | null | undefined): boolean =>
  BOT_UA.test(userAgent ?? "");
