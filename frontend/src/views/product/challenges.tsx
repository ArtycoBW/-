"use client";
import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { AppSelect } from "@/components/product/controls";
import { Modal } from "@/components/product/modal";
import { PageHead, useMessage } from "@/components/product/page";
import { Empty, Field, Notice, SelectSpec, Tag } from "@/components/product/ui";
import { api, post, User, Challenge, specName } from "@/lib/api";
import { specializations } from "@/lib/taxonomy";
import { MagnifyingGlass } from "@phosphor-icons/react";
import { PracticeScene } from "@/components/product/practice-scene";
export function Challenges({ user }: { user: User }) {
  const [items, setItems] = useState<Challenge[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState("all");
  const [query, setQuery] = useState("");
  const [direction, setDirection] = useState("");
  const [taskPage, setTaskPage] = useState(0);
  const [form, setForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [spec, setSpec] = useState("backend");
  const [rubric, setRubric] = useState(
    "Корректность — 40; граничные случаи — 30; тестирование — 20; ясность — 10.",
  );
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [reviews, setReviews] = useState<
    Record<string, { score: number; feedback: string }>
  >({});
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(
    () =>
      api<Challenge[]>("/challenges")
        .then(setItems)
        .catch((e) => setError(e.message)),
    [setError],
  );
  useEffect(() => {
    load();
  }, [load]);
  const filteredTasks = items.filter(
    (c) =>
      (!direction || c.specialization === direction) &&
      (status === "all" ||
        (status === "new"
          ? !c.submissions.length
          : status === "review"
            ? c.submissions.some((s) => s.score === null)
            : c.submissions.some((s) => s.score !== null))) &&
      `${c.title} ${c.description} ${c.company_name}`
        .toLocaleLowerCase("ru")
        .includes(query.trim().toLocaleLowerCase("ru")),
  );
  const currentTaskPage = Math.min(
    taskPage,
    Math.max(0, Math.ceil(filteredTasks.length / 6) - 1),
  );
  return (
    <>
      <PageHead
        eyebrow="ДЕРЖИТЕ НАВЫКИ В ФОРМЕ"
        title="Практика"
        text="Практические задачи от команд. Оценка по открытой рубрике, без изменения грейда."
        action={
          user.role === "employer" ? (
            <Button
              className="rz-button primary"
              onClick={() => setForm(!form)}
            >
              + Новое задание
            </Button>
          ) : undefined
        }
      />
      <section className="rz-practice-hero">
        <div>
          <span className="rz-kicker">Мастерская решений</span>
          <h2>Практика, которая остаётся в профиле</h2>
          <p>
            Выберите задачу команды. Объясните решение, проверьте крайние случаи
            и получите обратную связь по открытым критериям.
          </p>
          <div className="rz-practice-stats">
            <span>
              <b>{items.length}</b> задач
            </span>
            <span>
              <b>{items.filter((c) => c.submissions.length).length}</b>{" "}
              отправлено
            </span>
            <span>
              <b>
                {
                  items.filter((c) =>
                    c.submissions.some((s) => s.score !== null),
                  ).length
                }
              </b>{" "}
              с оценкой
            </span>
          </div>
        </div>
        <PracticeScene />
      </section>
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {form && (
        <form
          className="rz-panel rz-form rz-margin-bottom"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              await post("/challenges", {
                title,
                description,
                specialization: spec,
                rubric,
              });
              setForm(false);
              load();
            } catch (e) {
              setError((e as Error).message);
            }
          }}
        >
          <Field label="Название">
            <Input
              required
              minLength={3}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </Field>
          <Field label="Специализация">
            <SelectSpec value={spec} onChange={setSpec} />
          </Field>
          <Field label="Условие">
            <Textarea
              required
              minLength={20}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          <Field label="Рубрика оценки">
            <Textarea
              required
              minLength={10}
              value={rubric}
              onChange={(e) => setRubric(e.target.value)}
            />
          </Field>
          <Button className="rz-button primary">Опубликовать задание</Button>
        </form>
      )}
      <div className="rz-task-status" role="group" aria-label="Статус задания">
        {[
          ["all", "Все задачи"],
          ["new", "Доступные"],
          ["review", "На проверке"],
          ["done", "С оценкой"],
        ].map(([value, label]) => (
          <Button
            key={value}
            variant="ghost"
            aria-pressed={status === value}
            onClick={() => {
              setStatus(value);
              setTaskPage(0);
            }}
          >
            {label}
          </Button>
        ))}
      </div>
      <div className="rz-task-toolbar">
        <div className="rz-search">
          <MagnifyingGlass size={18} />
          <Input
            aria-label="Поиск заданий"
            placeholder="Задача или команда"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setTaskPage(0);
            }}
          />
        </div>
        <AppSelect
          aria-label="Направление задания"
          value={direction}
          onChange={(e) => {
            setDirection(e.target.value);
            setTaskPage(0);
          }}
        >
          <option value="">Все направления</option>
          {specializations
            .filter((spec) =>
              items.some((item) => item.specialization === spec.id),
            )
            .map((spec) => (
              <option key={spec.id} value={spec.id}>
                {spec.name}
              </option>
            ))}
        </AppSelect>
        <span className="rz-muted" aria-live="polite">
          Найдено заданий: {filteredTasks.length}
        </span>
      </div>
      {filteredTasks.length ? (
        <div className="rz-practice-grid">
          {filteredTasks
            .slice(currentTaskPage * 6, currentTaskPage * 6 + 6)
            .map((c, index) => (
              <article className="rz-practice-card" key={c.id}>
                <div className="rz-card-top">
                  <span className="rz-task-number">
                    {String(currentTaskPage * 6 + index + 1).padStart(2, "0")}
                  </span>
                  <Tag
                    tone={
                      c.submissions.some((s) => s.score !== null) ? "green" : ""
                    }
                  >
                    {c.submissions.length
                      ? c.submissions.some((s) => s.score !== null)
                        ? "С оценкой"
                        : "На проверке"
                      : "Можно решать"}
                  </Tag>
                </div>
                <p className="rz-job-direction">{specName(c.specialization)}</p>
                <h2>{c.title}</h2>
                <p className="rz-task-excerpt">{c.description}</p>
                <div className="rz-task-card-footer">
                  <span>{c.company_name}</span>
                  <Button
                    className="rz-button"
                    onClick={() => {
                      setSelectedId(c.id);
                      try {
                        const draft = localStorage.getItem(
                          `razryad.practice.${user.id}.${c.id}`,
                        );
                        if (draft) setAnswers((a) => ({ ...a, [c.id]: draft }));
                      } catch {}
                    }}
                  >
                    {c.submissions.length ? "Посмотреть" : "Решить задачу"}
                  </Button>
                </div>
              </article>
            ))}
        </div>
      ) : (
        <Empty title="Нет заданий по этим условиям">
          Попробуйте другой статус или измените поиск.
        </Empty>
      )}
      {selectedId &&
        items
          .filter((c) => c.id === selectedId)
          .map((c) => (
            <Modal
              wide
              key={c.id}
              title={c.title}
              onClose={() => setSelectedId(null)}
            >
              <section className="rz-practice-detail" key={c.id}>
                {state.error && <Notice error>{state.error}</Notice>}
                <div className="rz-card-top">
                  <Tag>{specName(c.specialization)}</Tag>
                  <span className="rz-muted">{c.company_name}</span>
                </div>
                <h2 className="rz-margin">{c.title}</h2>
                <p>{c.description}</p>
                <div className="rz-rubric">
                  <strong>Как оценивается</strong>
                  <p>{c.rubric}</p>
                </div>
                {user.role === "candidate" && !c.submissions.length && (
                  <form
                    className="rz-form"
                    onSubmit={async (e) => {
                      e.preventDefault();
                      setBusy(true);
                      try {
                        await post(`/challenges/${c.id}/submissions`, {
                          answer: answers[c.id] || "",
                        });
                        try {
                          localStorage.removeItem(
                            `razryad.practice.${user.id}.${c.id}`,
                          );
                        } catch {}
                        load();
                        state.setMessage(
                          "Решение отправлено на проверку работодателю",
                        );
                      } catch (e) {
                        setError((e as Error).message);
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    <Field label="Ваш подход к решению">
                      <Textarea
                        rows={4}
                        required
                        minLength={20}
                        maxLength={8000}
                        value={answers[c.id] || ""}
                        onChange={(e) => {
                          setAnswers({ ...answers, [c.id]: e.target.value });
                          try {
                            localStorage.setItem(
                              `razryad.practice.${user.id}.${c.id}`,
                              e.target.value,
                            );
                          } catch {}
                        }}
                      />
                    </Field>
                    <Button className="rz-button primary" disabled={state.busy}>
                      Отправить решение
                    </Button>
                  </form>
                )}
                {c.submissions.map((s) => (
                  <div className="rz-submission" key={s.id}>
                    <Tag tone={s.score !== null ? "green" : ""}>
                      {s.score === null
                        ? "Ожидает проверки"
                        : `${s.score} / 100`}
                    </Tag>
                    <p className="rz-prewrap">{s.answer}</p>
                    {s.feedback && <Notice>{s.feedback}</Notice>}
                    {user.role === "employer" && s.score === null && (
                      <form
                        className="rz-form"
                        onSubmit={async (e) => {
                          e.preventDefault();
                          try {
                            await post(
                              `/submissions/${s.id}/review`,
                              reviews[s.id] || { score: 0, feedback: "" },
                            );
                            load();
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      >
                        <Field label="Оценка 0–100">
                          <Input
                            type="number"
                            required
                            min={0}
                            max={100}
                            value={reviews[s.id]?.score ?? 0}
                            onChange={(e) =>
                              setReviews({
                                ...reviews,
                                [s.id]: {
                                  score: Number(e.target.value),
                                  feedback: reviews[s.id]?.feedback || "",
                                },
                              })
                            }
                          />
                        </Field>
                        <Field label="Обратная связь">
                          <Textarea
                            required
                            minLength={10}
                            value={reviews[s.id]?.feedback || ""}
                            onChange={(e) =>
                              setReviews({
                                ...reviews,
                                [s.id]: {
                                  score: reviews[s.id]?.score || 0,
                                  feedback: e.target.value,
                                },
                              })
                            }
                          />
                        </Field>
                        <Button className="rz-button">Оценить решение</Button>
                      </form>
                    )}
                  </div>
                ))}
              </section>
            </Modal>
          ))}
      {filteredTasks.length > 6 && (
        <div className="rz-pagination">
          <Button
            className="rz-button"
            disabled={currentTaskPage === 0}
            onClick={() => setTaskPage(currentTaskPage - 1)}
          >
            Назад
          </Button>
          <span>
            {currentTaskPage + 1} / {Math.ceil(filteredTasks.length / 6)}
          </span>
          <Button
            className="rz-button"
            disabled={(currentTaskPage + 1) * 6 >= filteredTasks.length}
            onClick={() => setTaskPage(currentTaskPage + 1)}
          >
            Далее
          </Button>
        </div>
      )}
    </>
  );
}
