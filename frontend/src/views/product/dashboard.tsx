"use client";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AppSelect, AppCheckbox } from "@/components/product/controls";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { ContactAccess } from "@/components/product/contact-access";
import {
  api,
  post,
  put,
  patch,
  User,
  Profile,
  Need,
  Invitation,
  Attempt,
  Application,
  Company,
  Challenge,
  gradeName,
  specName,
  formatName,
  statusName,
  money,
  date,
} from "@/lib/api";
import {
  Brand,
  Mark,
  Empty,
  Field,
  Notice,
  SelectGrade,
  SelectSpec,
  Skills,
  Tag,
} from "@/components/product/ui";

import {
  SquaresFour,
  UserCircle,
  Certificate,
  PaperPlaneTilt,
  Briefcase,
  ArrowsLeftRight,
  TerminalWindow,
  Buildings,
  UsersThree,
  List,
  Bell,
  Eye,
  CheckCircle,
  Clock,
  MapPin,
  Trophy,
  SidebarSimple,
  SignOut,
  Question,
  LockKey,
  CaretDown,
  MagnifyingGlass,
  BookmarkSimple,
  X,
} from "@phosphor-icons/react";
const navIcons = {
  overview: SquaresFour,
  profile: UserCircle,
  assessment: Certificate,
  invitations: PaperPlaneTilt,
  vacancies: Briefcase,
  applications: ArrowsLeftRight,
  challenges: TerminalWindow,
  company: Buildings,
  talent: UsersThree,
};

const candidateNav = [
  ["overview", "Обзор"],
  ["profile", "Мой профиль"],
  ["assessment", "Подтвердить уровень"],
  ["invitations", "Приглашения"],
  ["vacancies", "Вакансии"],
  ["applications", "Мои отклики"],
  ["challenges", "Практика"],
];
const employerNav = [
  ["overview", "Обзор"],
  ["talent", "Найти специалистов"],
  ["invitations", "Приглашения"],
  ["vacancies", "Мои вакансии"],
  ["applications", "Отклики"],
  ["challenges", "Задания команде"],
  ["company", "Моя компания"],
];

export function Dashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const section = pathname.split("/")[2] || "overview";
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [menu, setMenu] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return (
        typeof window !== "undefined" &&
        localStorage.getItem("razryad.sidebar") === "compact"
      );
    } catch {
      return false;
    }
  });
  function toggleSidebar() {
    setCollapsed((value) => {
      const next = !value;
      try {
        localStorage.setItem("razryad.sidebar", next ? "compact" : "full");
      } catch {}
      return next;
    });
  }
  async function logout() {
    try {
      await post("/auth/logout");
      router.push("/");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => router.replace("/auth"));
  }, [router]);
  useEffect(() => {
    const expired = () => router.replace("/auth?expired=1");
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, [router]);
  if (!user)
    return (
      <main className="rz-loading">
        <Mark />
        <p>Открываем ваш кабинет…</p>
      </main>
    );
  const nav = user.role === "candidate" ? candidateNav : employerNav;
  const label = nav.find((x) => x[0] === section)?.[1] || "Обзор";
  const profileHref =
    user.role === "candidate" ? "/app/profile" : "/app/company";
  return (
    <TooltipProvider delayDuration={250}>
      <div className={`rz-workspace ${collapsed ? "rz-compact" : ""}`}>
        <a href="#workspace-main" className="rz-skip">
          К содержимому
        </a>
        {menu && (
          <Button
            variant="ghost"
            className="rz-mobile-overlay"
            aria-label="Закрыть меню"
            onClick={() => setMenu(false)}
          />
        )}
        <aside className={`rz-sidebar ${menu ? "open" : ""}`}>
          <Brand />
          <div className="rz-space-label">
            <span className="rz-space-dot" />
            <span>{user.role === "candidate" ? "Карьера" : "Команда"}</span>
          </div>
          <nav aria-label="Разделы кабинета">
            {nav.map(([id, name]) => {
              const NavIcon = navIcons[id as keyof typeof navIcons];
              return (
                <Tooltip key={id}>
                  <TooltipTrigger asChild>
                    <Link
                      aria-label={name}
                      onClick={() => setMenu(false)}
                      href={id === "overview" ? "/app" : `/app/${id}`}
                      aria-current={section === id ? "page" : undefined}
                      className={section === id ? "active" : ""}
                    >
                      <NavIcon
                        size={21}
                        weight={section === id ? "duotone" : "regular"}
                        aria-hidden="true"
                      />
                      <span className="rz-nav-text">{name}</span>
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="rz-ui-popup">
                    {name}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </nav>
          <div className="rz-sidebar-bottom">
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/methodology" aria-label="Как работает подбор">
                  <Question size={20} />
                  <span className="rz-nav-text">Как работает подбор</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="rz-ui-popup">
                Как работает подбор
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/privacy-policy" aria-label="Приватность данных">
                  <LockKey size={20} />
                  <span className="rz-nav-text">Приватность данных</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="rz-ui-popup">
                Приватность данных
              </TooltipContent>
            </Tooltip>
            <div className="rz-account">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="rz-account-trigger"
                    aria-label="Меню аккаунта"
                  >
                    <span className="rz-avatar">
                      {user.email.slice(0, 2).toUpperCase()}
                    </span>
                    <span className="rz-nav-text">
                      <strong>
                        {user.role === "candidate"
                          ? "Личный кабинет"
                          : "Кабинет компании"}
                      </strong>
                      <small>{user.email}</small>
                    </span>
                    <CaretDown size={15} className="rz-account-caret" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="right"
                  align="end"
                  className="rz-ui-popup rz-account-menu"
                >
                  <DropdownMenuLabel>{user.email}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href={profileHref}>
                      <UserCircle size={18} />
                      {user.role === "candidate"
                        ? "Мой профиль"
                        : "Моя компания"}
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={logout}>
                    <SignOut size={18} />
                    Выйти из аккаунта
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </aside>
        <div className="rz-content">
          <header className="rz-topbar">
            <div>
              <Button
                variant="ghost"
                className="rz-collapse-button"
                aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"}
                aria-expanded={!collapsed}
                onClick={toggleSidebar}
              >
                <SidebarSimple size={21} />
              </Button>
              <Button
                variant="ghost"
                className="rz-menu-button"
                aria-label="Открыть меню"
                aria-expanded={menu}
                onClick={() => setMenu(!menu)}
              >
                <List size={22} />
              </Button>
              <span className="rz-muted">
                {user.role === "candidate" ? "Карьера" : "Команда"}
              </span>
              <span className="rz-breadcrumb">/</span>
              <strong>{label}</strong>
            </div>
            <div className="rz-topbar-actions">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    href="/app/invitations"
                    aria-label="Приглашения"
                    className="rz-icon-button"
                  >
                    <Bell size={20} />
                  </Link>
                </TooltipTrigger>
                <TooltipContent className="rz-ui-popup">
                  Приглашения
                </TooltipContent>
              </Tooltip>
              <Link
                href={profileHref}
                className="rz-top-avatar"
                aria-label="Открыть профиль"
              >
                {user.email[0].toUpperCase()}
              </Link>
            </div>
          </header>
          <main id="workspace-main" className="rz-main">
            <div key={section} className="rz-route">
              {error && <Notice error>{error}</Notice>}
              {section === "overview" ? (
                <Overview user={user} />
              ) : section === "profile" && user.role === "candidate" ? (
                <ProfileEditor />
              ) : section === "assessment" && user.role === "candidate" ? (
                <Assessment />
              ) : section === "talent" && user.role === "employer" ? (
                <Talent />
              ) : section === "invitations" ? (
                <Invitations user={user} />
              ) : section === "vacancies" ? (
                <Vacancies user={user} />
              ) : section === "applications" ? (
                <Applications user={user} />
              ) : section === "company" && user.role === "employer" ? (
                <CompanyEditor />
              ) : section === "challenges" ? (
                <Challenges user={user} />
              ) : (
                <Empty title="Раздел недоступен">
                  Выберите раздел в меню своего кабинета.
                </Empty>
              )}
            </div>
          </main>
          <footer className="rz-app-footer">
            <span>Разряд · профиль, навыки, работа</span>
            <Link href="/privacy-policy">О данных платформы</Link>
          </footer>
        </div>
      </div>
    </TooltipProvider>
  );
}

function PageHead({
  eyebrow,
  title,
  text,
  action,
}: {
  eyebrow: string;
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rz-pagehead">
      <div>
        <p className="rz-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="rz-muted">{text}</p>
      </div>
      {action}
    </div>
  );
}
function useMessage() {
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  return { error, setError, message, setMessage, busy, setBusy };
}

function Overview({ user }: { user: User }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [candidates, setCandidates] = useState<Profile[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [invitedProfile, setInvitedProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    Promise.all([
      api<Invitation[]>("/invitations").then(setInvitations),
      user.role === "candidate"
        ? api<Profile>("/profile").then(setProfile)
        : Promise.all([
            api<Company>("/company").then(setCompany),
            api<{ items: Profile[]; total: number }>(
              "/candidates?limit=3",
            ).then((x) => {
              setCandidates(x.items);
              setTotal(x.total);
            }),
          ]),
    ]).catch((e) => setError(e.message));
  }, [user.role]);
  const candidate = user.role === "candidate";
  return (
    <>
      <PageHead
        eyebrow={candidate ? "Личный кабинет" : "Рабочее пространство команды"}
        title={
          candidate
            ? `Здравствуйте${profile ? ", " + profile.name.split(" ")[0] : ""}.`
            : `Подбор специалистов`
        }
        text={
          candidate
            ? "Управляйте профилем и выбирайте предложения от компаний."
            : `${company?.name || "Ваша компания"} · потребности, приглашения и отклики в одном месте.`
        }
        action={
          <Link
            className="rz-button primary"
            href={candidate ? "/app/assessment" : "/app/talent"}
          >
            {candidate ? "Подтвердить уровень" : "Найти специалиста"}
          </Link>
        }
      />
      {error && <Notice error>{error}</Notice>}
      <div className="rz-stats">
        <div>
          <span>
            {candidate ? "ПОДТВЕРЖДЁННЫЙ УРОВЕНЬ" : "СПЕЦИАЛИСТОВ В БАНКЕ"}
          </span>
          <strong>
            {candidate ? gradeName(profile?.grade || null) : total}
            <i></i>
          </strong>
          <small>
            {candidate
              ? specName(profile?.specialization || "backend")
              : "Только опубликованные и проверенные"}
          </small>
        </div>
        <div>
          <span>
            {candidate ? "РЕЗУЛЬТАТ ТЕСТА" : "ПРИГЛАШЕНИЙ ОТПРАВЛЕНО"}
          </span>
          <strong>
            {candidate ? profile?.score || "—" : invitations.length}
            <em>{candidate ? "/ 100" : ""}</em>
          </strong>
          <small>
            {candidate
              ? `Проверено ${date(profile?.verified_at || null)}`
              : "Все условия известны заранее"}
          </small>
        </div>
        <div>
          <span>{candidate ? "НОВЫХ ПРИГЛАШЕНИЙ" : "ПРИНЯТО ПРЕДЛОЖЕНИЙ"}</span>
          <strong>
            {
              invitations.filter((x) =>
                candidate
                  ? ["sent", "viewed"].includes(x.status)
                  : x.status === "accepted",
              ).length
            }
            <span className="rz-live-dot" />
          </strong>
          <small>
            {candidate
              ? "Ожидают вашего решения"
              : "Контакты доступны после согласия"}
          </small>
        </div>
      </div>
      <div className="rz-overview-grid">
        <section className="rz-feature-panel">
          <p className="rz-eyebrow">
            {candidate ? "ПРОФИЛЬ СПЕЦИАЛИСТА" : "ПРОФИЛЬ КОМПАНИИ"}
          </p>
          <h2>
            {candidate
              ? profile?.name || "Ваш профиль"
              : company?.name || "Ваша команда"}
          </h2>
          <p>
            {candidate
              ? `${specName(profile?.specialization || "backend")} · ${gradeName(profile?.grade || null)}. ${profile?.city || "Укажите город в профиле"}`
              : "Сохраните требования к роли. Сравните стек, результаты тестов и подтверждённые достижения в одной подборке."}
          </p>
          {candidate && profile && (
            <Skills items={profile.skills.slice(0, 5)} />
          )}
          <div className="rz-profile-summary">
            <span>
              {candidate ? "Публикация профиля" : "Принцип отбора"}
              <strong>
                {candidate
                  ? profile?.published
                    ? "Виден работодателям"
                    : "Пока скрыт"
                  : "Специализация + грейд"}
              </strong>
            </span>
            <span>
              {candidate ? "Желаемая зарплата" : "Контакты кандидата"}
              <strong>
                {candidate
                  ? `от ${money(profile?.salary_min || 0)} ₽`
                  : "После его согласия"}
              </strong>
            </span>
          </div>
          <Link
            className="rz-button"
            href={candidate ? "/app/profile" : "/app/talent"}
          >
            {candidate ? "Посмотреть профиль" : "Собрать подборку"}
          </Link>
          <div className="rz-signal-graphic" aria-hidden="true">
            <span>ПРОФИЛЬ</span>
            <i />
            <b></b>
            <i />
            <span>ВОЗМОЖНОСТЬ</span>
          </div>
        </section>
        <section className="rz-panel">
          <div className="rz-section-title">
            <h2>{candidate ? "Следующие действия" : "Принципы подбора"}</h2>
            <Tag>03 шага</Tag>
          </div>
          <div className="rz-step">
            <b>01</b>
            <div>
              <strong>
                {candidate ? "Расскажите о себе" : "Опишите потребность"}
              </strong>
              <p>
                {candidate
                  ? "Стек, опыт и карьерные ожидания"
                  : "Категория, задачи и открытая зарплата"}
              </p>
            </div>
            <span>✓</span>
          </div>
          <div className="rz-step">
            <b>02</b>
            <div>
              <strong>
                {candidate ? "Подтвердите навыки" : "Сравните доказательства"}
              </strong>
              <p>
                {candidate
                  ? "Сопоставимые задачи и честный результат"
                  : "Тест, навыки и достижения ФСП"}
              </p>
            </div>
            <span>{profile?.grade || !candidate ? "✓" : "○"}</span>
          </div>
          <div className="rz-step">
            <b>03</b>
            <div>
              <strong>
                {candidate ? "Выберите предложение" : "Начните с предложения"}
              </strong>
              <p>Контакт открывается после согласия</p>
            </div>
            <span></span>
          </div>
          <Link className="rz-text-link" href="/methodology">
            Узнать о методике
          </Link>
        </section>
      </div>
      <div className="rz-section-title">
        <h2>{candidate ? "Предложения для вас" : "Специалисты в подборке"}</h2>
        <Link href={candidate ? "/app/invitations" : "/app/talent"}>
          Посмотреть все
        </Link>
      </div>
      {candidate ? (
        invitations.length ? (
          <div className="rz-card-grid">
            {invitations.slice(0, 3).map((i) => (
              <div className="rz-card" key={i.id}>
                <div className="rz-card-top">
                  <span className="rz-company-icon">
                    <Buildings size={22} />
                  </span>
                  <Tag tone={i.status === "accepted" ? "green" : ""}>
                    {statusName(i.status)}
                  </Tag>
                </div>
                <p className="rz-muted">{i.company_name}</p>
                <h3>{i.title}</h3>
                <p className="rz-salary">
                  {money(i.salary_min)} – {money(i.salary_max)} ₽
                </p>
                <Link href="/app/invitations" className="rz-text-link">
                  Обсудить предложение
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <Empty title="Ваши предложения ещё впереди">
            Опубликуйте профиль и подтвердите уровень, чтобы компании могли вас
            найти.
          </Empty>
        )
      ) : (
        <div className="rz-card-grid">
          {candidates.map((p) => (
            <TalentCard
              key={p.id}
              profile={p}
              onInvite={() => setInvitedProfile(p)}
            />
          ))}
        </div>
      )}
      {message && <Notice>{message}</Notice>}
      {invitedProfile && <InviteModal profile={invitedProfile} onClose={() => setInvitedProfile(null)} onDone={() => {
        setInvitedProfile(null);
        setMessage("Приглашение отправлено. Контакты откроются после принятия.");
        api<Invitation[]>("/invitations").then(setInvitations).catch(e => setError(e.message));
      }} />}
    </>
  );
}

function ProfileEditor() {
  const [p, setP] = useState<Profile | null>(null);
  const [skills, setSkills] = useState("");
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(
    () =>
      api<Profile>("/profile")
        .then((x) => {
          setP(x);
          setSkills(x.skills.join(", "));
        })
        .catch((e) => setError(e.message)),
    [setError],
  );
  useEffect(() => {
    load();
  }, [load]);
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!p) return;
    setBusy(true);
    setError("");
    try {
      const fields = {
        name: p.name,
        city: p.city,
        bio: p.bio,
        contact: p.contact || "",
        specialization: p.specialization,
        desired_grade: p.desired_grade,
        skills: skills
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
        experience: p.experience,
        work_format: p.work_format,
        salary_min: p.salary_min,
        published: p.published,
        consent: p.consent,
      };
      setP(await put<Profile>("/profile", fields));
      state.setMessage("Профиль сохранён");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!p)
    return (
      <>
        {state.error ? (
          <Notice error>{state.error}</Notice>
        ) : (
          <p>Загружаем профиль…</p>
        )}
      </>
    );
  function change<K extends keyof Profile>(key: K, value: Profile[K]) {
    setP((old) => (old ? { ...old, [key]: value } : old));
  }
  return (
    <>
      <PageHead
        eyebrow="ПРОФИЛЬ СПЕЦИАЛИСТА"
        title="Мой профиль"
        text="Самоописание рассказывает о вас. Тест и достижения подтверждают навыки."
        action={
          <a href="/api/v1/profile/pdf" className="rz-button">
            Скачать PDF
          </a>
        }
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      <div className="rz-profile-grid">
        <form className="rz-panel rz-form" onSubmit={save}>
          <h2>Основная информация</h2>
          <div className="rz-two">
            <Field label="Имя и фамилия">
              <Input
                required
                minLength={2}
                maxLength={120}
                value={p.name}
                onChange={(e) => change("name", e.target.value)}
              />
            </Field>
            <Field label="Город">
              <Input
                maxLength={120}
                value={p.city}
                onChange={(e) => change("city", e.target.value)}
              />
            </Field>
          </div>
          <div className="rz-two">
            <Field label="Специализация">
              <SelectSpec
                value={p.specialization}
                onChange={(v) => change("specialization", v)}
              />
            </Field>
            <Field label="Предполагаемый уровень">
              <SelectGrade
                value={p.desired_grade}
                onChange={(v) => change("desired_grade", v)}
              />
            </Field>
          </div>
          <Field
            label="Навыки через запятую"
            hint="Например: Python, FastAPI, PostgreSQL"
          >
            <Input
              required
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
            />
          </Field>
          <div className="rz-two">
            <Field label="Опыт, лет">
              <Input
                type="number"
                min={0}
                max={60}
                value={p.experience}
                onChange={(e) => change("experience", Number(e.target.value))}
              />
            </Field>
            <Field label="Желаемая зарплата от, ₽">
              <Input
                type="number"
                min={0}
                max={10000000}
                value={p.salary_min}
                onChange={(e) => change("salary_min", Number(e.target.value))}
              />
            </Field>
          </div>
          <Field label="Формат работы">
            <AppSelect
              value={p.work_format}
              onChange={(e) => change("work_format", e.target.value)}
            >
              <option value="remote">Удалённо</option>
              <option value="hybrid">Гибрид</option>
              <option value="office">В офисе</option>
            </AppSelect>
          </Field>
          <Field label="О себе">
            <Textarea
              rows={5}
              maxLength={3000}
              value={p.bio}
              onChange={(e) => change("bio", e.target.value)}
            />
          </Field>
          <Field
            label="Контакт для связи"
            hint="Скрыт до принятия приглашения или вашего отклика"
          >
            <Input
              maxLength={250}
              value={p.contact || ""}
              onChange={(e) => change("contact", e.target.value)}
            />
          </Field>
          <label className="rz-check">
            <AppCheckbox
              checked={p.consent}
              onChange={(e) => {
                change("consent", e.target.checked);
                if (!e.target.checked) change("published", false);
              }}
            />
            <span>Согласен на обработку данных профиля</span>
          </label>
          <label className="rz-check">
            <AppCheckbox
              checked={p.published}
              onChange={(e) => change("published", e.target.checked)}
            />
            <span>
              Показывать мой профиль работодателям после подтверждения уровня
            </span>
          </label>
          <Button className="rz-button primary" disabled={state.busy}>
            {state.busy ? "Сохраняем…" : "Сохранить профиль"}
          </Button>
        </form>
        <aside className="rz-stack">
          <ContactAccess />
          <section className="rz-panel">
            <Tag tone="green">{gradeName(p.grade)}</Tag>
            <h2 className="rz-margin">Подтверждённый уровень</h2>
            <p className="rz-muted">
              {p.grade
                ? `${p.score} / 100 · ${date(p.verified_at)}`
                : "Пройдите тест, чтобы ваш профиль появился в банке специалистов."}
            </p>
            <Link href="/app/assessment" className="rz-text-link">
              Открыть тестирование
            </Link>
          </section>
          <section className="rz-panel">
            <h2>Резюме в PDF</h2>
            <p className="rz-muted">
              Распознаем текст и навыки. Перед сохранением проверьте каждое
              поле.
            </p>
            <label className="rz-button rz-upload">
              Загрузить резюме
              <Input
                type="file"
                accept="application/pdf"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setError("");
                  const form = new FormData();
                  form.append("file", file);
                  try {
                    const r = await api<{
                      name: string;
                      bio: string;
                      contact: string;
                      skills: string[];
                      notice: string;
                    }>("/profile/import-pdf", { method: "POST", body: form });
                    setP({
                      ...p,
                      name: r.name,
                      bio: r.bio,
                      contact: r.contact,
                    });
                    setSkills(r.skills.join(", "));
                    state.setMessage(r.notice);
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              />
            </label>
          </section>
          <section className="rz-panel">
            <div className="rz-section-title">
              <h2>Профиль ФСП</h2>
              <Tag>Демо</Tag>
            </div>
            {p.achievements.length ? (
              p.achievements.map((a) => (
                <div className="rz-achievement" key={a.id}>
                  <b>♜ {a.place} место</b>
                  <p>{a.title}</p>
                  <small>
                    {a.discipline} · {a.date}
                  </small>
                </div>
              ))
            ) : (
              <p className="rz-muted">
                Нет связанной истории. Это не мешает получать предложения.
              </p>
            )}
            <div className="rz-actions">
              <Button
                className="rz-button"
                onClick={async () => {
                  try {
                    setP(
                      await post<Profile>("/integrations/fsp", {
                        participant_id: "DEMO-FSP-2026",
                      }),
                    );
                    state.setMessage(
                      "Подключён демонстрационный реестр. Это не официальная проверка ФСП.",
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Связать демо-ID
              </Button>
              {p.fsp_id && (
                <Button
                  className="rz-text-link"
                  onClick={async () => {
                    try {
                      setP(
                        await api<Profile>("/integrations/fsp", {
                          method: "DELETE",
                        }),
                      );
                    } catch (e) {
                      setError((e as Error).message);
                    }
                  }}
                >
                  Отвязать
                </Button>
              )}
            </div>
            <small className="rz-muted">
              Официальное подключение ожидает API ФСП.
            </small>
          </section>
        </aside>
      </div>
    </>
  );
}

function Assessment() {
  const [history, setHistory] = useState<Attempt[]>([]);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [spec, setSpec] = useState("backend");
  const [grade, setGrade] = useState("middle");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [now, setNow] = useState(() => Date.now());
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(
    () =>
      api<Attempt[]>("/assessments")
        .then((rows) => {
          setHistory(rows);
          const active = rows.find(
            (a) => !a.submitted_at && a.expires_at * 1000 > Date.now(),
          );
          if (active) {
            setAttempt(active);
            setAnswers(active.answers);
          }
        })
        .catch((e) => setError(e.message)),
    [setError],
  );
  useEffect(() => {
    load();
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [load]);
  async function start() {
    setBusy(true);
    setError("");
    try {
      const a = await post<Attempt>("/assessments", {
        specialization: spec,
        grade,
      });
      setAttempt(a);
      setAnswers(a.answers);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submit() {
    if (!attempt) return;
    setBusy(true);
    setError("");
    try {
      const a = await post<Attempt>(`/assessments/${attempt.id}/submit`, {
        answers,
      });
      setAttempt(a);
      setHistory(await api<Attempt[]>("/assessments"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const remaining = attempt
    ? Math.max(0, Math.floor((attempt.expires_at * 1000 - now) / 1000))
    : 0;
  return (
    <>
      <PageHead
        eyebrow="ПОДТВЕРЖДЕНИЕ КОМПЕТЕНЦИЙ"
        title="Подтвердить уровень"
        text="Выберите направление и грейд. В тесте 8 вопросов, на выполнение 30 минут."
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {!attempt ? (
        <div className="rz-two">
          <section className="rz-panel rz-form">
            <h2>Выберите ваш уровень</h2>
            <Field label="Специализация">
              <SelectSpec value={spec} onChange={setSpec} />
            </Field>
            <Field label="Уровень, который хотите подтвердить">
              <SelectGrade value={grade} onChange={setGrade} />
            </Field>
            <Button
              className="rz-button primary"
              disabled={state.busy}
              onClick={start}
            >
              Начать тест
            </Button>
            <small className="rz-muted">
              Перед началом заполните навыки и согласия в профиле.
            </small>
          </section>
          <section className="rz-panel">
            <h2>Что вас ждёт</h2>
            <div className="rz-step">
              <b>08</b>
              <div>
                <strong>Практических вопросов</strong>
                <p>Алгоритмы, данные, технологии и надёжность</p>
              </div>
            </div>
            <div className="rz-step">
              <b>30</b>
              <div>
                <strong>Минут на попытку</strong>
                <p>Перезагрузка страницы не сбрасывает таймер</p>
              </div>
            </div>
            <div className="rz-step">
              <b>70%</b>
              <div>
                <strong>Для подтверждения</strong>
                <p>Неудача не понижает ваш текущий грейд</p>
              </div>
            </div>
            <Link href="/methodology" className="rz-text-link">
              Полная методика
            </Link>
          </section>
        </div>
      ) : attempt.submitted_at ? (
        <section className="rz-panel rz-result">
          <span className="rz-result-score">
            {attempt.score}
            <small>/100</small>
          </span>
          <Tag tone={attempt.passed ? "green" : ""}>
            {attempt.passed ? "Уровень подтверждён" : "Попробуйте ещё раз"}
          </Tag>
          <h2>
            {attempt.passed
              ? `${specName(attempt.specialization)} · ${gradeName(attempt.grade)}`
              : "Эта попытка не подтвердила уровень"}
          </h2>
          <p>
            {attempt.passed
              ? "Результат сохранён в профиле. Следующая смена грейда доступна через 90 дней."
              : "Ваш прежний грейд сохранён. При первой проверке можно выбрать уровень ниже; повтор этого уровня — через сутки."}
          </p>
          {(attempt.score || 0) >= 90 && (
            <Notice>
              Сильный результат! После окончания интервала можно попробовать
              более высокий уровень.
            </Notice>
          )}
          <div className="rz-tags">
            {attempt.outcomes?.map((x, i) => (
              <Tag key={x.id} tone={x.correct ? "green" : ""}>
                {i + 1}. {x.skill} {x.correct ? "✓" : "—"}
              </Tag>
            ))}
          </div>
          <div className="rz-actions">
            <Link href="/app/profile" className="rz-button primary">
              Мой профиль
            </Link>
            <Button className="rz-button" onClick={() => setAttempt(null)}>
              К выбору уровня
            </Button>
          </div>
        </section>
      ) : (
        <section className="rz-panel">
          <div className="rz-section-title">
            <h2>
              {specName(attempt.specialization)} · {gradeName(attempt.grade)}
            </h2>
            <Tag tone={remaining < 120 ? "red" : ""}>
              {Math.floor(remaining / 60)}:
              {String(remaining % 60).padStart(2, "0")}
            </Tag>
          </div>
          <p className="rz-muted">
            Введите числовой ответ. Сохранение черновика позволяет продолжить
            после перезагрузки.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
          >
            {attempt.questions.map((q, i) => (
              <div className="rz-question" key={q.id}>
                <div>
                  <Tag>
                    {String(i + 1).padStart(2, "0")} / {q.skill}
                  </Tag>
                  <p>{q.text}</p>
                </div>
                <Field label={`Ответ на вопрос ${i + 1}`}>
                  <Input
                    inputMode="decimal"
                    value={answers[q.id] || ""}
                    maxLength={50}
                    onChange={(e) =>
                      setAnswers({ ...answers, [q.id]: e.target.value })
                    }
                  />
                </Field>
              </div>
            ))}
            <div className="rz-actions">
              <Button className="rz-button primary" disabled={state.busy}>
                Завершить и проверить
              </Button>
              <Button
                type="button"
                disabled={state.busy || remaining === 0}
                className="rz-button"
                onClick={async () => {
                  try {
                    await put(`/assessments/${attempt.id}/answers`, {
                      answers,
                    });
                    state.setMessage("Черновик сохранён");
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Сохранить черновик
              </Button>
            </div>
          </form>
        </section>
      )}
      {history.length > 0 && (
        <section className="rz-panel rz-margin">
          <h2>История попыток</h2>
          <div className="rz-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Специализация</th>
                  <th>Уровень</th>
                  <th>Результат</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {history.map((a) => (
                  <tr key={a.id}>
                    <td>{specName(a.specialization)}</td>
                    <td>{gradeName(a.grade)}</td>
                    <td>{a.score ?? "—"}</td>
                    <td>
                      {a.submitted_at
                        ? a.passed
                          ? "Подтверждён"
                          : "Не подтверждён"
                        : a.expires_at * 1000 < now
                          ? "Время истекло"
                          : "В процессе"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}

function TalentCard({
  profile: p,
  onInvite,
  onDetails,
}: {
  profile: Profile;
  onInvite: () => void;
  onDetails?: () => void;
}) {
  return (
    <article className="rz-card rz-talent-card">
      <div className="rz-talent-main">
        <div className="rz-person-heading">
          <span className="rz-person-avatar" aria-hidden="true">
            {p.name
              .split(" ")
              .slice(0, 2)
              .map((x) => x[0])
              .join("")}
          </span>
          <div>
            <h3>
              {p.name}{" "}
              <CheckCircle
                size={18}
                weight="fill"
                className="rz-person-verified"
                aria-label="Грейд подтверждён"
              />
            </h3>
            <p className="rz-muted">
              {specName(p.specialization)} · {gradeName(p.grade)}
            </p>
          </div>
        </div>
        <Skills items={p.skills} />
        <div className="rz-person-facts">
          <span>
            <MapPin size={15} /> {p.city || "Город не указан"}
          </span>
          <span>
            <Clock size={15} /> Опыт: {p.experience} лет
          </span>
          <span>
            <Certificate size={15} /> Тест: {p.score}/100
          </span>
          {p.achievements.length > 0 && (
            <span>
              <Trophy size={15} /> ФСП · демореестр
            </span>
          )}
        </div>
      </div>
      <aside className="rz-talent-actions">
        {p.match && (
          <div className="rz-match">
            <strong>{p.match.score}</strong>
            <small>баллов соответствия</small>
          </div>
        )}
        <strong className="rz-person-salary">от {money(p.salary_min)} ₽</strong>
        <div>
          {onDetails && <Button
            className="rz-icon-button"
            aria-label={`Подробнее: ${p.name}`}
            onClick={onDetails}
          >
            <Eye size={19} />
          </Button>}
          <Button className="rz-button small primary" onClick={onInvite}>
            Пригласить
          </Button>
        </div>
      </aside>
      {p.match && (
        <details className="rz-explanation">
          <summary>Почему в подборке?</summary>
          {p.match.explanation.map((x) => (
            <p key={x}>{x}</p>
          ))}
          {p.match.missing_skills.length > 0 && (
            <p>Не указаны: {p.match.missing_skills.join(", ")}</p>
          )}
          <dl className="rz-factor-list">
            {p.match.factors.map((factor) => (
              <div key={factor.key}>
                <dt>
                  {(
                    {
                      skills: "Совпадение стека",
                      test: "Результат теста",
                      grade: "Категория",
                      freshness: "Активность",
                      fsp: "Достижения ФСП",
                      format: "Формат работы",
                    } as Record<string, string>
                  )[factor.key] ?? factor.key}
                </dt>
                <dd>+{factor.contribution.toLocaleString("ru-RU")}</dd>
              </div>
            ))}
          </dl>
          {p.match.baseline_score !== undefined && (
            <p>
              Формула: {p.match.baseline_score.toLocaleString("ru-RU")} балла.
              {p.match.learned_score !== null &&
              p.match.learned_score !== undefined
                ? ` Итог: 70% формулы + 30% оценки модели (${p.match.learned_score.toLocaleString("ru-RU")}).`
                : " Модель недоступна — используется формула."}
            </p>
          )}
          <small>
            Самоописанный стек учитывается вместе с подтверждённым тестом.
            Модель обучена на синтетике; балл не является вероятностью найма.
          </small>
        </details>
      )}
    </article>
  );
}

const initialNeed = {
  title: "Python-разработчик",
  description:
    "Развиваем API продуктовой платформы. Нужны опыт работы с базами данных и внимательность к качеству.",
  specialization: "backend",
  grade: "middle",
  skills: ["Python", "FastAPI", "PostgreSQL"],
  work_format: "remote",
  salary_min: 180000,
  salary_max: 260000,
};
function NeedFields({
  value: v,
  onChange,
}: {
  value: typeof initialNeed;
  onChange: (v: typeof initialNeed) => void;
}) {
  return (
    <>
      <Field label="Название роли">
        <Input
          required
          minLength={3}
          maxLength={160}
          value={v.title}
          onChange={(e) => onChange({ ...v, title: e.target.value })}
        />
      </Field>
      <div className="rz-two">
        <Field label="Специализация">
          <SelectSpec
            value={v.specialization}
            onChange={(x) => onChange({ ...v, specialization: x })}
          />
        </Field>
        <Field label="Грейд">
          <SelectGrade
            value={v.grade}
            onChange={(x) => onChange({ ...v, grade: x })}
          />
        </Field>
      </div>
      <Field label="Навыки через запятую">
        <Input
          required
          value={v.skills.join(",")}
          onChange={(e) =>
            onChange({ ...v, skills: e.target.value.split(",") })
          }
        />
      </Field>
      <Field label="Задачи и ожидания">
        <Textarea
          rows={4}
          required
          minLength={10}
          maxLength={5000}
          value={v.description}
          onChange={(e) => onChange({ ...v, description: e.target.value })}
        />
      </Field>
      <div className="rz-two">
        <Field label="Зарплата от, ₽">
          <Input
            type="number"
            required
            min={1}
            max={10000000}
            value={v.salary_min}
            onChange={(e) =>
              onChange({ ...v, salary_min: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="Зарплата до, ₽">
          <Input
            type="number"
            required
            min={v.salary_min || 1}
            max={10000000}
            value={v.salary_max}
            onChange={(e) =>
              onChange({ ...v, salary_max: Number(e.target.value) })
            }
          />
        </Field>
      </div>
      <Field label="Формат работы">
        <AppSelect
          value={v.work_format}
          onChange={(e) => onChange({ ...v, work_format: e.target.value })}
        >
          <option value="remote">Удалённо</option>
          <option value="hybrid">Гибрид</option>
          <option value="office">В офисе</option>
        </AppSelect>
      </Field>
      <small className="rz-muted">Суммы в месяц, до вычета налогов.</small>
    </>
  );
}

function Talent() {
  const params = useSearchParams();
  const [items, setItems] = useState<Profile[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const requestNumber = useRef(0);
  const [needs, setNeeds] = useState<Need[]>([]);
  const [need, setNeed] = useState(params.get("need") || "");
  const [spec, setSpec] = useState(params.get("spec") || "");
  const [grade, setGrade] = useState(params.get("grade") || "");
  const [skill, setSkill] = useState(params.get("skill") || "");
  const [fsp, setFsp] = useState(params.get("fsp") === "true");
  const [form, setForm] = useState(false);
  const [values, setValues] = useState(initialNeed);
  const [selected, setSelected] = useState<Profile | null>(null);
  const [details, setDetails] = useState<Profile | null>(null);
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(async () => {
    const request = ++requestNumber.current;
    setBusy(true);
    setError("");
    const q = new URLSearchParams({ offset: String(page * 12), limit: "12" });
    if (need) q.set("need_id", need);
    if (spec) q.set("specialization", spec);
    if (grade) q.set("grade", grade);
    if (skill) q.set("skill", skill);
    if (fsp) q.set("fsp", "true");
    try {
      const r = await api<{ items: Profile[]; total: number }>(
        `/candidates?${q}`,
      );
      if (request !== requestNumber.current) return;
      setItems(r.items);
      setTotal(r.total);
    } catch (e) {
      if (request === requestNumber.current) setError((e as Error).message);
    } finally {
      if (request === requestNumber.current) setBusy(false);
    }
  }, [need, spec, grade, skill, fsp, page, setError, setBusy]);
  useEffect(() => {
    setPage(0);
  }, [need, spec, grade, skill, fsp]);
  useEffect(() => {
    api<Need[]>("/needs")
      .then(setNeeds)
      .catch((e) => setError(e.message));
  }, [setError]);
  useEffect(() => {
    const timer = setTimeout(() => {
      load();
      const q = new URLSearchParams();
      if (need) q.set("need", need);
      if (spec) q.set("spec", spec);
      if (grade) q.set("grade", grade);
      if (skill) q.set("skill", skill);
      if (fsp) q.set("fsp", "true");
      const query = q.toString();
      const url = `/app/talent${query ? `?${query}` : ""}`;
      if (`${window.location.pathname}${window.location.search}` !== url) {
        window.history.replaceState(null, "", url);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [load, need, spec, grade, skill, fsp]);
  return (
    <>
      <PageHead
        eyebrow="БАНК ПОДТВЕРЖДЁННЫХ КОМПЕТЕНЦИЙ"
        title="Найти специалистов"
        text="Выберите требования к роли и сравните подтверждённые навыки."
        action={
          <Button className="rz-button primary" onClick={() => setForm(!form)}>
            + Описать потребность
          </Button>
        }
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {form && (
        <form
          className="rz-panel rz-form rz-margin-bottom"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              const n = await post<Need>("/needs", values);
              setNeeds([n, ...needs]);
              setNeed(n.id);
              setSpec("");
              setGrade("");
              setForm(false);
              state.setMessage("Потребность сохранена. Подборка готова.");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <h2>Кого ищет ваша команда?</h2>
          <NeedFields value={values} onChange={setValues} />
          <Button className="rz-button primary" disabled={state.busy}>
            Сохранить и подобрать
          </Button>
        </form>
      )}
      <div className="rz-filterbar">
        <label className="rz-search">
          <MagnifyingGlass size={18} aria-hidden="true" />
          <Input
            aria-label="Поиск по навыку"
            placeholder="Навык, например Python"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          />
        </label>
        <AppSelect
          aria-label="Сохранённая потребность"
          value={need}
          onChange={(e) => {
            setNeed(e.target.value);
            setSpec("");
            setGrade("");
          }}
        >
          <option value="">Все специалисты</option>
          {needs.map((n) => (
            <option value={n.id} key={n.id}>
              {n.title} · {gradeName(n.grade)}
            </option>
          ))}
        </AppSelect>
        <AppSelect
          aria-label="Специализация"
          value={spec}
          onChange={(e) => setSpec(e.target.value)}
        >
          <option value="">Все направления</option>
          <option value="backend">Бэкенд</option>
          <option value="frontend">Фронтенд</option>
        </AppSelect>
        <AppSelect
          aria-label="Грейд"
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
        >
          <option value="">Все уровни</option>
          <option value="junior">Начальный</option>
          <option value="middle">Средний</option>
          <option value="senior">Старший</option>
        </AppSelect>
      </div>
      <div className="rz-results-bar">
        <p>
          <strong>{total}</strong> специалистов{" "}
          <span className="rz-muted">
            {state.busy
              ? "· обновляем подборку…"
              : "· по соответствию потребности"}
          </span>
        </p>
        <label className="rz-check">
          <AppCheckbox
            checked={fsp}
            onChange={(e) => setFsp(e.target.checked)}
          />
          <span>С достижениями ФСП</span>
        </label>
      </div>
      {items.length ? (
        <div className="rz-card-grid">
          {items.map((p) => (
            <TalentCard
              key={p.id}
              profile={p}
              onInvite={() => setSelected(p)}
              onDetails={() => setDetails(p)}
            />
          ))}
        </div>
      ) : (
        <Empty
          title={
            state.busy ? "Собираем подборку…" : "Пока нет точных совпадений"
          }
        >
          Попробуйте другую категорию или уберите часть фильтров. Сохранённая
          потребность останется доступна.
        </Empty>
      )}
      {total > 12 && (
        <div className="rz-pagination">
          <Button
            className="rz-button"
            disabled={page === 0 || state.busy}
            onClick={() => setPage(page - 1)}
          >
            Назад
          </Button>
          <span>
            {page + 1} / {Math.ceil(total / 12)}
          </span>
          <Button
            className="rz-button"
            disabled={(page + 1) * 12 >= total || state.busy}
            onClick={() => setPage(page + 1)}
          >
            Далее
          </Button>
        </div>
      )}
      {selected && (
        <InviteModal
          profile={selected}
          onClose={() => setSelected(null)}
          onDone={() => {
            setSelected(null);
            state.setMessage(
              "Приглашение отправлено. Контакты откроются после принятия.",
            );
          }}
        />
      )}
      {details && (
        <Modal title={details.name} onClose={() => setDetails(null)}>
          <Tag tone="green">
            {gradeName(details.grade)} · тест {details.score}/100
          </Tag>
          <p>{details.bio}</p>
          <Skills items={details.skills} />
          <p>
            {details.city} · {formatName(details.work_format)}
          </p>
          {details.achievements.map((a) => (
            <p key={a.id}>
              ♜ {a.title} · {a.place} место
            </p>
          ))}
          <Notice>
            Контакты скрыты до принятия приглашения. Достижения в этом стенде —
            из демонстрационного реестра.
          </Notice>
          <Button
            className="rz-button primary"
            onClick={() => {
              setSelected(details);
              setDetails(null);
            }}
          >
            Пригласить специалиста
          </Button>
        </Modal>
      )}
    </>
  );
}

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  const returnFocus = useRef<HTMLElement | null>(null);
  const heading = useRef<HTMLHeadingElement | null>(null);
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent
        className="rz-dialog"
        aria-describedby={undefined}
        onOpenAutoFocus={(event) => {
          event.preventDefault();
          returnFocus.current = document.activeElement as HTMLElement;
          heading.current?.focus();
        }}
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          returnFocus.current?.focus({ preventScroll: true });
        }}
      >
        <DialogHeader>
          <DialogTitle ref={heading} tabIndex={-1}>
            {title}
          </DialogTitle>
        </DialogHeader>
        <div className="rz-dialog-body">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
function InviteModal({
  profile,
  onClose,
  onDone,
}: {
  profile: Profile;
  onClose: () => void;
  onDone: () => void;
}) {
  const [title, setTitle] = useState(
    `${specName(profile.specialization)} в нашу команду`,
  );
  const [message, setMessage] = useState(
    `Здравствуйте, ${profile.name.split(" ")[0]}! Нам понравился ваш подтверждённый профиль. Приглашаем обсудить задачи и познакомиться с командой.`,
  );
  const [low, setLow] = useState(profile.salary_min);
  const [high, setHigh] = useState(Math.round(profile.salary_min * 1.3));
  const [contact, setContact] = useState("");
  const state = useMessage();
  const { setError, setBusy } = state;
  useEffect(() => {
    api<Company>("/company")
      .then((c) => setContact(c.contact))
      .catch(() => {});
  }, []);
  return (
    <Modal title="Начните со своего предложения" onClose={onClose}>
      <p className="rz-muted">
        {profile.name} · {gradeName(profile.grade)}
      </p>
      {state.error && <Notice error>{state.error}</Notice>}
      <form
        className="rz-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          try {
            await post("/invitations", {
              candidate_id: profile.id,
              title,
              message,
              contact,
              salary_min: low,
              salary_max: high,
            });
            onDone();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <Field label="Роль и команда">
          <Input
            required
            minLength={3}
            maxLength={160}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </Field>
        <Field label="Расскажите о предложении">
          <Textarea
            required
            rows={4}
            minLength={10}
            maxLength={3000}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
        </Field>
        <div className="rz-two">
          <Field label="Зарплата от, ₽">
            <Input
              required
              type="number"
              min={1}
              value={low}
              onChange={(e) => setLow(Number(e.target.value))}
            />
          </Field>
          <Field label="Зарплата до, ₽">
            <Input
              required
              type="number"
              min={low}
              value={high}
              onChange={(e) => setHigh(Number(e.target.value))}
            />
          </Field>
        </div>
        <Field label="Контакт компании">
          <Input
            required
            minLength={3}
            maxLength={250}
            value={contact}
            onChange={(e) => setContact(e.target.value)}
          />
        </Field>
        <small className="rz-muted">
          Зарплата до вычета налогов. Контакты специалиста откроются только
          после его согласия.
        </small>
        <Button
          className="rz-button primary"
          disabled={state.busy || !contact.trim() || low < 1 || high < low}
        >
          Отправить приглашение
        </Button>
      </form>
    </Modal>
  );
}

function Invitations({ user }: { user: User }) {
  const [items, setItems] = useState<Invitation[]>([]);
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(
    () =>
      api<Invitation[]>("/invitations")
        .then(setItems)
        .catch((e) => setError(e.message)),
    [setError],
  );
  useEffect(() => {
    load();
  }, [load]);
  async function act(id: string, status: string) {
    setBusy(true);
    setError("");
    try {
      await patch(`/invitations/${id}`, { status });
      await load();
      state.setMessage(
        status === "accepted"
          ? "Предложение принято. Только эта компания получила доступ к вашим контактам."
          : "Статус обновлён",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHead
        eyebrow="ЗНАКОМСТВО НА ВАШИХ УСЛОВИЯХ"
        title={
          user.role === "candidate"
            ? "Приглашения для вас"
            : "Отправленные приглашения"
        }
        text="Зарплата и задачи известны заранее. Решение всегда остаётся за специалистом."
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {items.length ? (
        <div className="rz-stack">
          {items.map((i) => (
            <article className="rz-panel" key={i.id}>
              <div className="rz-card-top">
                <p className="rz-eyebrow">
                  {i.company_name} {i.candidate_name}
                </p>
                <Tag tone={i.status === "accepted" ? "green" : ""}>
                  {statusName(i.status)}
                </Tag>
              </div>
              <h2>{i.title}</h2>
              <p className="rz-salary">
                {money(i.salary_min)} – {money(i.salary_max)} ₽{" "}
                <small>в месяц, до вычета налогов</small>
              </p>
              <p className="rz-prewrap">{i.message}</p>
              <div className="rz-invite-meta">
                <span>Контакт компании: {i.contact}</span>
                <span>{date(i.created_at)}</span>
              </div>
              {i.contacts_unlocked && user.role === "employer" && (
                <Notice>
                  Контакт специалиста: {i.candidate_email} ·{" "}
                  {i.candidate_contact}
                </Notice>
              )}
              {["sent", "viewed"].includes(i.status) && (
                <div className="rz-actions">
                  {user.role === "candidate" ? (
                    <>
                      <Button
                        disabled={state.busy}
                        className="rz-button primary"
                        onClick={() => act(i.id, "accepted")}
                      >
                        Принять и открыть контакты
                      </Button>
                      <Button
                        disabled={state.busy}
                        className="rz-button"
                        onClick={() => act(i.id, "declined")}
                      >
                        Отклонить
                      </Button>
                      {i.status === "sent" && (
                        <Button
                          disabled={state.busy}
                          className="rz-text-link"
                          onClick={() => act(i.id, "viewed")}
                        >
                          Отметить просмотренным
                        </Button>
                      )}
                    </>
                  ) : (
                    <Button
                      className="rz-button"
                      disabled={state.busy}
                      onClick={() => act(i.id, "withdrawn")}
                    >
                      Отозвать приглашение
                    </Button>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>
      ) : (
        <Empty title="Здесь появятся приглашения">
          {user.role === "candidate"
            ? "Подтвердите уровень и включите публикацию профиля."
            : "Откройте банк специалистов и отправьте первое предложение."}
        </Empty>
      )}
    </>
  );
}

function Vacancies({ user }: { user: User }) {
  const [items, setItems] = useState<Need[]>([]);
  const [q, setQ] = useState("");
  const [vacSpec, setVacSpec] = useState("");
  const [vacGrade, setVacGrade] = useState("");
  const [vacFormat, setVacFormat] = useState("");
  const [page, setPage] = useState(0);
  const [savedOnly, setSavedOnly] = useState(false);
  const [saved, setSaved] = useState<string[]>(() => {
    try {
      const value = JSON.parse(
        localStorage.getItem(`razryad.saved.${user.id}`) || "[]",
      );
      return Array.isArray(value)
        ? value.filter((x) => typeof x === "string")
        : [];
    } catch {
      return [];
    }
  });
  const [loading, setLoading] = useState(true);
  const request = useRef(0);
  function toggleSaved(id: string) {
    setSaved((old) => {
      const next = old.includes(id)
        ? old.filter((x) => x !== id)
        : [...old, id];
      try {
        localStorage.setItem(`razryad.saved.${user.id}`, JSON.stringify(next));
      } catch {}
      return next;
    });
  }
  const [form, setForm] = useState(false);
  const [editing, setEditing] = useState("");
  const [values, setValues] = useState(initialNeed);
  const [selected, setSelected] = useState<Need | null>(null);
  const [letter, setLetter] = useState("");
  const [share, setShare] = useState(false);
  const state = useMessage();
  const { setError, setBusy } = state;
  const employer = user.role === "employer";
  const load = useCallback(async () => {
    const current = ++request.current;
    setLoading(true);
    try {
      let rows: Need[] = [];
      if (employer) rows = await api<Need[]>("/company/vacancies");
      else {
        let offset = 0;
        while (true) {
          const batch = await api<{ items: Need[]; total: number }>(
            `/vacancies?limit=100&offset=${offset}`,
          );
          if (current !== request.current) return;
          rows.push(...batch.items);
          offset += batch.items.length;
          if (!batch.items.length || offset >= batch.total) break;
        }
      }
      if (current === request.current) setItems(rows);
    } catch (e) {
      if (current === request.current) setError((e as Error).message);
    } finally {
      if (current === request.current) setLoading(false);
    }
  }, [employer, setError]);
  const cancelLoad = useCallback(() => {
    request.current++;
  }, []);
  useEffect(() => {
    load();
    return cancelLoad;
  }, [load, cancelLoad]);
  const filtered = items.filter(
    (v) =>
      (!vacSpec || v.specialization === vacSpec) &&
      (!vacGrade || v.grade === vacGrade) &&
      (!vacFormat || v.work_format === vacFormat) &&
      (!savedOnly || saved.includes(v.id)) &&
      `${v.title} ${v.company_name || ""} ${v.skills.join(" ")}`
        .toLowerCase()
        .includes(q.toLowerCase()),
  );
  const currentPage = Math.min(
    page,
    Math.max(0, Math.ceil(filtered.length / 12) - 1),
  );
  const visible = filtered.slice(currentPage * 12, (currentPage + 1) * 12);
  return (
    <>
      <PageHead
        eyebrow="ОТКРЫТЫЕ ВОЗМОЖНОСТИ"
        title={employer ? "Вакансии компании" : "Открытые вакансии"}
        text={
          employer
            ? "Публикуйте вакансии с прозрачными условиями и работайте с откликами."
            : "Найдите команду по стеку, уровню и условиям. Зарплата известна до первого разговора."
        }
        action={
          employer ? (
            <Button
              className="rz-button primary"
              onClick={() => {
                setEditing("");
                setValues(initialNeed);
                setForm(!form);
              }}
            >
              + Новая вакансия
            </Button>
          ) : undefined
        }
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {form && (
        <form
          className="rz-panel rz-form rz-margin-bottom"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              if (editing) await put(`/vacancies/${editing}`, values);
              else await post("/vacancies", values);
              setForm(false);
              load();
              state.setMessage("Вакансия сохранена");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <h2>{editing ? "Редактировать вакансию" : "Новая вакансия"}</h2>
          <NeedFields value={values} onChange={setValues} />
          <Button className="rz-button primary" disabled={state.busy}>
            Сохранить вакансию
          </Button>
        </form>
      )}
      {!employer && (
        <div className="rz-list-tabs" aria-label="Список вакансий">
          <Button
            variant="ghost"
            aria-pressed={!savedOnly}
            onClick={() => {
              setSavedOnly(false);
              setPage(0);
            }}
          >
            Все вакансии <span>{items.length}</span>
          </Button>
          <Button
            variant="ghost"
            aria-pressed={savedOnly}
            onClick={() => {
              setSavedOnly(true);
              setPage(0);
            }}
          >
            <BookmarkSimple size={16} />
            Избранное <span>{saved.length}</span>
          </Button>
        </div>
      )}
      <div className="rz-vacancy-toolbar">
        <label className="rz-search">
          <MagnifyingGlass size={18} aria-hidden="true" />
          <Input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            placeholder="Роль, компания или навык"
            aria-label="Поиск вакансий"
          />
        </label>
        <AppSelect
          aria-label="Направление вакансии"
          value={vacSpec}
          onChange={(e) => {
            setVacSpec(e.target.value);
            setPage(0);
          }}
        >
          <option value="">Все направления</option>
          <option value="backend">Бэкенд</option>
          <option value="frontend">Фронтенд</option>
        </AppSelect>
        <AppSelect
          aria-label="Уровень вакансии"
          value={vacGrade}
          onChange={(e) => {
            setVacGrade(e.target.value);
            setPage(0);
          }}
        >
          <option value="">Любой уровень</option>
          <option value="junior">Junior</option>
          <option value="middle">Middle</option>
          <option value="senior">Senior</option>
        </AppSelect>
        <AppSelect
          aria-label="Формат вакансии"
          value={vacFormat}
          onChange={(e) => {
            setVacFormat(e.target.value);
            setPage(0);
          }}
        >
          <option value="">Любой формат</option>
          <option value="remote">Удалённо</option>
          <option value="hybrid">Гибрид</option>
          <option value="office">Офис</option>
        </AppSelect>
      </div>
      <div className="rz-results-bar">
        <span aria-live="polite">
          {loading
            ? "Загружаем вакансии…"
            : `Найдено вакансий: ${filtered.length}`}
        </span>
        {(q || vacSpec || vacGrade || vacFormat) && (
          <Button
            variant="ghost"
            className="rz-text-link"
            onClick={() => {
              setQ("");
              setVacSpec("");
              setVacGrade("");
              setVacFormat("");
              setPage(0);
            }}
          >
            <X size={14} />
            Сбросить фильтры
          </Button>
        )}
      </div>
      {loading ? (
        <div className="rz-list-skeleton" aria-label="Загрузка вакансий">
          <div />
          <div />
          <div />
        </div>
      ) : visible.length ? (
        <div className="rz-vacancy-list">
          {visible.map((v) => (
            <article className="rz-vacancy-row" key={v.id}>
              <span className="rz-company-icon" aria-hidden="true">
                {(v.company_name || "Компания")
                  .split(" ")
                  .slice(0, 2)
                  .map((x) => x[0])
                  .join("")}
              </span>
              <div>
                <p className="rz-vacancy-company">
                  {v.company_name || "Ваша компания"}
                </p>
                <h3>{v.title}</h3>
                <div className="rz-vacancy-meta">
                  <span>
                    <Briefcase size={14} />
                    {gradeName(v.grade)}
                  </span>
                  <span>
                    <MapPin size={14} />
                    {formatName(v.work_format)}
                  </span>
                  {v.archived && <Tag>В архиве</Tag>}
                </div>
                <Skills items={v.skills} />
                <p className="rz-vacancy-description">{v.description}</p>
              </div>
              <div className="rz-vacancy-aside">
                <p className="rz-salary">
                  {money(v.salary_min)} – {money(v.salary_max)} ₽
                </p>
                <small>в месяц · до вычета налогов</small>
                <div className="rz-actions">
                  {employer ? (
                    <>
                      <Button
                        className="rz-button"
                        onClick={() => {
                          setValues(v);
                          setEditing(v.id);
                          setForm(true);
                          window.scrollTo(0, 0);
                        }}
                      >
                        Изменить
                      </Button>
                      <Button
                        className="rz-text-link"
                        onClick={async () => {
                          try {
                            await patch(`/vacancies/${v.id}`, {
                              status: v.archived ? "published" : "archived",
                            });
                            load();
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      >
                        {v.archived ? "Опубликовать" : "В архив"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            className="rz-bookmark"
                            aria-label={
                              saved.includes(v.id)
                                ? "Убрать из избранного"
                                : "Сохранить вакансию"
                            }
                            aria-pressed={saved.includes(v.id)}
                            onClick={() => toggleSaved(v.id)}
                          >
                            <BookmarkSimple
                              size={18}
                              weight={saved.includes(v.id) ? "fill" : "regular"}
                            />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="rz-ui-popup">
                          {saved.includes(v.id) ? "Сохранено" : "В избранное"}
                        </TooltipContent>
                      </Tooltip>
                      <Button
                        className="rz-button primary"
                        onClick={() => {
                          setSelected(v);
                          setShare(false);
                          setLetter("");
                          setError("");
                        }}
                      >
                        Подробнее
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty
          title={
            savedOnly
              ? "Вы ещё не сохранили вакансии"
              : "По этим условиям вакансий нет"
          }
        >
          {savedOnly
            ? "Нажмите на закладку рядом с подходящей ролью. Избранное сохраняется в этом браузере."
            : "Попробуйте убрать один из фильтров или изменить поисковый запрос."}
        </Empty>
      )}
      {filtered.length > 12 && (
        <div className="rz-pagination">
          <Button
            className="rz-button"
            disabled={currentPage === 0}
            onClick={() => {
              setPage(currentPage - 1);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            Назад
          </Button>
          <span>
            {currentPage + 1} / {Math.ceil(filtered.length / 12)}
          </span>
          <Button
            className="rz-button"
            disabled={(currentPage + 1) * 12 >= filtered.length}
            onClick={() => {
              setPage(currentPage + 1);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            Далее
          </Button>
        </div>
      )}
      {selected && (
        <Modal title={selected.title} onClose={() => setSelected(null)}>
          <p className="rz-salary">
            {money(selected.salary_min)} – {money(selected.salary_max)} ₽
          </p>
          <div className="rz-vacancy-meta">
            <span>{selected.company_name}</span>
            <span>{formatName(selected.work_format)}</span>
            <span>{gradeName(selected.grade)}</span>
          </div>
          <p>{selected.description}</p>
          {state.error && <Notice error>{state.error}</Notice>}
          <Skills items={selected.skills} />
          <form
            className="rz-form"
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              try {
                await post(`/vacancies/${selected.id}/applications`, {
                  letter,
                  share_contacts: share,
                });
                setSelected(null);
                state.setMessage(
                  "Отклик отправлен. Контакты доступны только компании этой вакансии.",
                );
              } catch (e) {
                setError((e as Error).message);
                setSelected(null);
              } finally {
                setBusy(false);
              }
            }}
          >
            <Field label="Сопроводительное письмо">
              <Textarea
                rows={3}
                maxLength={2000}
                value={letter}
                onChange={(e) => setLetter(e.target.value)}
              />
            </Field>
            <label className="rz-check">
              <AppCheckbox
                required
                checked={share}
                onChange={(e) => setShare(e.target.checked)}
              />
              <span>
                Разрешаю передать контакты компании «{selected.company_name}»
              </span>
            </label>
            <Button disabled={state.busy} className="rz-button primary">
              Отправить отклик
            </Button>
          </form>
        </Modal>
      )}
    </>
  );
}

function Applications({ user }: { user: User }) {
  const [items, setItems] = useState<Application[]>([]);
  const state = useMessage();
  const { setError, setBusy } = state;
  const load = useCallback(
    () =>
      api<Application[]>("/applications")
        .then(setItems)
        .catch((e) => setError(e.message)),
    [setError],
  );
  useEffect(() => {
    load();
  }, [load]);
  return (
    <>
      <PageHead
        eyebrow="ДВИЖЕНИЕ К ЗНАКОМСТВУ"
        title="Отклики"
        text="Следите за статусами откликов и продолжайте общение с подходящей командой."
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {items.length ? (
        <div className="rz-stack">
          {items.map((a) => (
            <section className="rz-panel" key={a.id}>
              <div className="rz-card-top">
                <h2>{a.vacancy_title}</h2>
                <Tag>{statusName(a.status)}</Tag>
              </div>
              <p className="rz-muted">
                {a.company_name} · {a.candidate_name}
              </p>
              <p>{a.letter || "Без сопроводительного письма"}</p>
              {a.candidate && (
                <Notice>
                  {a.candidate.email} · {a.candidate.contact}
                </Notice>
              )}
              {!["withdrawn", "rejected"].includes(a.status) && (
                <div className="rz-actions">
                  {(user.role === "candidate"
                    ? ["withdrawn"]
                    : ["reviewing", "interview", "rejected"]
                  ).map((status) => (
                    <Button
                      className="rz-button"
                      disabled={state.busy}
                      key={status}
                      onClick={async () => {
                        setBusy(true);
                        try {
                          await patch(`/applications/${a.id}`, { status });
                          load();
                        } catch (e) {
                          setError((e as Error).message);
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      {statusName(status)}
                    </Button>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      ) : (
        <Empty title="Пока нет откликов">
          {user.role === "candidate"
            ? "Найдите интересную вакансию и расскажите о себе."
            : "Опубликуйте вакансию с понятными задачами и зарплатой."}
        </Empty>
      )}
    </>
  );
}

function CompanyEditor() {
  const [value, setValue] = useState<Company | null>(null);
  const state = useMessage();
  const { setError, setBusy } = state;
  useEffect(() => {
    api<Company>("/company")
      .then(setValue)
      .catch((e) => setError(e.message));
  }, [setError]);
  return (
    <>
      <PageHead
        eyebrow="ЛИЦО ВАШЕЙ КОМАНДЫ"
        title="Профиль компании"
        text="Понятное описание компании помогает специалисту принять решение."
      />
      {state.error && <Notice error>{state.error}</Notice>}
      {state.message && <Notice>{state.message}</Notice>}
      {value && (
        <form
          className="rz-panel rz-form rz-form-narrow"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              const { name, description, industry, city, contact } = value;
              await put("/company", {
                name,
                description,
                industry,
                city,
                contact,
              });
              state.setMessage("Профиль компании сохранён");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {(
            [
              ["name", "Название компании"],
              ["industry", "Направление деятельности"],
              ["city", "Город"],
              ["contact", "Контакт для связи"],
            ] as const
          ).map(([key, label]) => (
            <Field key={key} label={label}>
              <Input
                required={key !== "city"}
                value={value[key]}
                onChange={(e) => setValue({ ...value, [key]: e.target.value })}
                maxLength={key === "contact" ? 250 : 120}
              />
            </Field>
          ))}
          <Field label="О команде и продукте">
            <Textarea
              rows={6}
              maxLength={3000}
              value={value.description}
              onChange={(e) =>
                setValue({ ...value, description: e.target.value })
              }
            />
          </Field>
          <Button className="rz-button primary" disabled={state.busy}>
            Сохранить изменения
          </Button>
          <Notice>
            Профиль компании в прототипе не означает независимую проверку
            юридического лица.
          </Notice>
        </form>
      )}
    </>
  );
}

function Challenges({ user }: { user: User }) {
  const [items, setItems] = useState<Challenge[]>([]);
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
          <option value="backend">Бэкенд-разработка</option>
          <option value="frontend">Фронтенд-разработка</option>
        </AppSelect>
        <span className="rz-muted" aria-live="polite">
          Найдено заданий: {filteredTasks.length}
        </span>
      </div>
      {filteredTasks.length ? (
        <div className="rz-stack">
          {filteredTasks
            .slice(currentTaskPage * 6, currentTaskPage * 6 + 6)
            .map((c) => (
              <section className="rz-panel" key={c.id}>
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
                        onChange={(e) =>
                          setAnswers({ ...answers, [c.id]: e.target.value })
                        }
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
            ))}
        </div>
      ) : (
        <Empty title="Новых задач пока нет">
          Здесь появятся задания по вашей специализации.
        </Empty>
      )}
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
