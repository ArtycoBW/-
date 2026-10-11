"use client";

import { useState } from "react";
import { MagnifyingGlass, X } from "@phosphor-icons/react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AppSelect } from "./controls";
import { statusName } from "@/lib/api";

type Entry = {
  id: string;
  status: string;
  created_at: number;
  salary_max?: number;
};
const normalize = (value: string) =>
  value.toLocaleLowerCase("ru").replaceAll("ё", "е").trim();

export function useCollection<T extends Entry>(
  items: T[],
  searchable: (item: T) => string,
) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("newest");
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const filtered = items
    .filter(
      (item) =>
        (!status || item.status === status) &&
        words.every((word) => normalize(searchable(item)).includes(word)),
    )
    .sort((a, b) =>
      sort === "salary"
        ? (b.salary_max || 0) - (a.salary_max || 0) ||
          b.created_at - a.created_at
        : sort === "oldest"
          ? a.created_at - b.created_at
          : b.created_at - a.created_at,
    );
  function reset() {
    setQuery("");
    setStatus("");
    setSort("newest");
  }
  return {
    query,
    setQuery,
    status,
    setStatus,
    sort,
    setSort,
    reset,
    filtered,
    total: items.length,
    active: !!query || !!status || sort !== "newest",
  };
}

export function CollectionFilters<T extends Entry>({
  collection: c,
  items,
  statuses,
  label,
  salary = false,
}: {
  collection: ReturnType<typeof useCollection<T>>;
  items: T[];
  statuses: string[];
  label: string;
  salary?: boolean;
}) {
  return (
    <section className="rz-collection-tools" aria-label="Поиск и фильтры">
      <div className="rz-collection-inputs">
        <label className="rz-collection-search">
          <MagnifyingGlass size={20} aria-hidden />
          <Input
            type="search"
            aria-label={label}
            placeholder={label}
            value={c.query}
            onChange={(e) => c.setQuery(e.target.value)}
          />
        </label>
        <AppSelect
          aria-label="Статус"
          value={c.status}
          onChange={(e) => c.setStatus(e.target.value)}
        >
          <option value="">Все статусы · {items.length}</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {statusName(status)} ·{" "}
              {items.filter((item) => item.status === status).length}
            </option>
          ))}
        </AppSelect>
        <AppSelect
          aria-label="Сортировка"
          value={c.sort}
          onChange={(e) => c.setSort(e.target.value)}
        >
          <option value="newest">Сначала новые</option>
          <option value="oldest">Сначала старые</option>
          {salary && <option value="salary">По зарплате ↓</option>}
        </AppSelect>
      </div>
      <div className="rz-collection-summary">
        <span aria-live="polite">
          Найдено: {c.filtered.length} из {c.total}
        </span>
        {c.active && (
          <Button type="button" className="rz-text-link" onClick={c.reset}>
            <X size={14} aria-hidden /> Сбросить фильтры
          </Button>
        )}
      </div>
    </section>
  );
}
