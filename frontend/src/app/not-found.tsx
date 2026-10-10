import Link from "next/link";

/**
 * 404 page. Rendered for unmatched routes and `notFound()` calls; Next serves
 * it with a 404 status, so crawlers see a proper not-found response.
 */
export default function NotFound() {
  return (
    <div className="rz-loading">
      <h1 className="text-6xl font-bold">404</h1>
      <p className="text-lg">Страница не найдена.</p>
      <Link href="/" className="underline underline-offset-4">
        На главную
      </Link>
    </div>
  );
}
