"use client";

import { useId, useRef, useState, type ReactNode } from "react";
import {
  Code,
  ListChecks,
  ListBullets,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  DownloadSimple,
  PencilSimple,
  Eye,
} from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { type Challenge, specName } from "@/lib/api";
import { Tag } from "./ui";

const MAX_LENGTH = 8000;
const snippets = {
  plan: "## Подход\n\n## Основные шаги\n1. \n2. \n3. \n\n## Ограничения и сложность\n",
  code: "```\n// Код или псевдокод решения\n```\n",
  tests:
    "## Проверка решения\n- Обычный случай: вход → ожидаемый результат\n- Граничный случай: вход → ожидаемый результат\n- Ошибка: как обрабатываем\n",
};

// Deliberately renders text, headings, lists and fenced code only; never HTML.
export function SolutionPreview({ value }: { value: string }) {
  const blocks: ReactNode[] = [];
  const lines = value.split("\n");
  let code: string[] | null = null;
  let language = "";
  let paragraph: string[] = [];
  let list: string[] = [];
  const flush = () => {
    if (paragraph.length) {
      blocks.push(<p key={blocks.length}>{paragraph.join("\n")}</p>);
      paragraph = [];
    }
    if (list.length) {
      blocks.push(
        <ul key={blocks.length}>
          {list.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>,
      );
      list = [];
    }
  };
  for (const line of lines) {
    if (line.trimStart().startsWith("```")) {
      flush();
      if (code !== null) {
        blocks.push(
          <div className="rz-solution-code" key={blocks.length}>
            <span>{language || "Код / псевдокод"}</span>
            <pre>
              <code>{code.join("\n")}</code>
            </pre>
          </div>,
        );
        code = null;
      } else {
        code = [];
        language = line.trim().slice(3);
      }
    } else if (code !== null) code.push(line);
    else if (/^#{1,3}\s/.test(line)) {
      flush();
      blocks.push(
        <h3 key={blocks.length}>{line.replace(/^#{1,3}\s+/, "")}</h3>,
      );
    } else if (/^\s*(?:[-*]|\d+\.)\s/.test(line)) {
      if (paragraph.length) flush();
      list.push(line.replace(/^\s*(?:[-*]|\d+\.)\s+/, ""));
    } else if (!line.trim()) flush();
    else {
      if (list.length) flush();
      paragraph.push(line);
    }
  }
  flush();
  if (code !== null)
    blocks.push(
      <pre key={blocks.length}>
        <code>{code.join("\n")}</code>
      </pre>,
    );
  return (
    <div className="rz-solution-preview">
      {blocks.length ? (
        blocks
      ) : (
        <p className="rz-editor-empty">
          Здесь появится ваше решение. Начните с подхода, добавьте код и опишите
          проверку.
        </p>
      )}
    </div>
  );
}

export function PracticeWorkbench({
  challenge,
  userId,
  onSubmit,
}: {
  challenge: Challenge;
  userId: string;
  onSubmit: (answer: string) => Promise<void>;
}) {
  const draftKey = `razryad.practice.${userId}.${challenge.id}`;
  const [answer, setAnswer] = useState(() => {
    try {
      return localStorage.getItem(draftKey) || "";
    } catch {
      return "";
    }
  });
  const [saved, setSaved] = useState<"idle" | "saved" | "failed">("idle");
  const [preview, setPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const editor = useRef<HTMLTextAreaElement>(null);
  const editorId = useId();
  const canSend = answer.trim().length >= 20 && answer.length <= MAX_LENGTH;
  function update(value: string) {
    setAnswer(value);
    setError("");
    try {
      localStorage.setItem(draftKey, value);
      setSaved("saved");
    } catch {
      setSaved("failed");
    }
  }
  function insert(kind: keyof typeof snippets) {
    const field = editor.current;
    const start = field?.selectionStart ?? answer.length;
    const end = field?.selectionEnd ?? start;
    const addition = `${start && answer[start - 1] !== "\n" ? "\n\n" : ""}${snippets[kind]}`;
    const value = answer.slice(0, start) + addition + answer.slice(end);
    if (value.length > MAX_LENGTH) {
      setError("Для вставки не хватает места: максимум 8 000 символов.");
      return;
    }
    update(value);
    requestAnimationFrame(() => {
      field?.focus();
      field?.setSelectionRange(
        start + addition.length,
        start + addition.length,
      );
    });
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([answer], { type: "text/markdown;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "razryad-solution.md";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function send() {
    if (!canSend || busy) return;
    setBusy(true);
    setError("");
    try {
      await onSubmit(answer);
      try {
        localStorage.removeItem(draftKey);
      } catch {}
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="rz-workbench">
      <aside className="rz-workbench-brief" aria-label="Условие и критерии">
        <div className="rz-workbench-meta">
          <Tag>{specName(challenge.specialization)}</Tag>
          <span>{challenge.company_name}</span>
        </div>
        <section>
          <p className="rz-workbench-kicker">01 / Задача</p>
          <h3>Что нужно сделать</h3>
          <p className="rz-workbench-description">{challenge.description}</p>
        </section>
        <section className="rz-workbench-rubric">
          <p className="rz-workbench-kicker">02 / Критерии</p>
          <h3>Как оценят решение</h3>
          <p>{challenge.rubric}</p>
        </section>
        <div className="rz-workbench-note">
          <CheckCircle size={20} aria-hidden="true" />
          <p>
            Решение проверит команда. Баллы останутся в практике и не изменят
            ваш грейд.
          </p>
        </div>
      </aside>
      <section className="rz-workbench-compose" aria-label="Рабочее место">
        <header className="rz-editor-heading">
          <div>
            <p className="rz-workbench-kicker">03 / Ваше решение</p>
            <h3>{preview ? "Перед отправкой" : "От идеи к решению"}</h3>
          </div>
          <span className="rz-editor-draft-label">Черновик</span>
        </header>
        <div
          className="rz-editor-modes"
          role="group"
          aria-label="Режим редактора"
        >
          <Button
            type="button"
            aria-pressed={!preview}
            disabled={busy}
            onClick={() => setPreview(false)}
          >
            <PencilSimple size={17} />
            Редактор
          </Button>
          <Button
            type="button"
            aria-pressed={preview}
            disabled={busy}
            onClick={() => setPreview(true)}
          >
            <Eye size={18} />
            Предпросмотр
          </Button>
          <Button
            type="button"
            className="rz-editor-download"
            disabled={!answer || busy}
            onClick={download}
            aria-label="Скачать решение в Markdown"
          >
            <DownloadSimple size={18} />
            <span>Скачать</span>
          </Button>
        </div>
        {!preview ? (
          <div className="rz-editor-surface">
            <div className="rz-editor-tools" aria-label="Шаблоны решения">
              <span>Добавить</span>
              <Button
                type="button"
                disabled={busy}
                onClick={() => insert("plan")}
              >
                <ListBullets size={16} />
                План
              </Button>
              <Button
                type="button"
                disabled={busy}
                onClick={() => insert("code")}
              >
                <Code size={18} />
                Код
              </Button>
              <Button
                type="button"
                disabled={busy}
                onClick={() => insert("tests")}
              >
                <ListChecks size={18} />
                Тест-кейсы
              </Button>
            </div>
            <label className="sr-only" htmlFor={editorId}>
              Ваш подход к решению
            </label>
            <textarea
              id={editorId}
              ref={editor}
              disabled={busy}
              spellCheck={false}
              value={answer}
              maxLength={MAX_LENGTH}
              onChange={(e) => update(e.target.value)}
              aria-describedby={`${editorId}-hint`}
              placeholder={
                "Сначала опишите идею: почему этот подход решает задачу?\n\nЗатем добавьте реализацию или псевдокод и примеры проверки.\n\nМожно начать с плана на панели выше."
              }
            />
            <div className="rz-editor-hint" id={`${editorId}-hint`}>
              <span>Текст · заголовки ## · блоки кода ```</span>
              <span>{answer.length.toLocaleString("ru-RU")} / 8 000</span>
            </div>
          </div>
        ) : (
          <div className="rz-editor-review">
            <p className="rz-review-hint">
              Так команда увидит ваше решение. Проверьте логику, крайние случаи
              и примеры.
            </p>
            <SolutionPreview value={answer} />
          </div>
        )}
        <div
          className={`rz-editor-save ${saved === "failed" ? "is-error" : ""}`}
          role="status"
        >
          {saved === "failed"
            ? "Не удалось сохранить на устройстве. Скачайте копию перед закрытием."
            : saved === "saved"
              ? "Черновик сохранён на этом устройстве"
              : answer
                ? "Черновик восстановлен с этого устройства"
                : "Черновик сохраняется автоматически на этом устройстве"}
        </div>
        {error && (
          <p role="alert" className="rz-editor-error">
            {error}
          </p>
        )}
        <footer className="rz-editor-footer">
          <p>
            {!canSend
              ? "Минимум 20 символов содержательного решения."
              : "После отправки решение нельзя изменить."}
          </p>
          {preview ? (
            <div>
              <Button
                type="button"
                className="rz-button"
                disabled={busy}
                onClick={() => setPreview(false)}
              >
                <ArrowLeft size={16} />
                Править
              </Button>
              <Button
                type="button"
                className="rz-button primary"
                disabled={!canSend || busy}
                onClick={send}
              >
                {busy ? "Отправляем…" : "Отправить решение"}
                <ArrowRight size={17} />
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              className="rz-button primary"
              disabled={!canSend}
              onClick={() => setPreview(true)}
            >
              Проверить решение
              <ArrowRight size={17} />
            </Button>
          )}
        </footer>
      </section>
    </div>
  );
}
