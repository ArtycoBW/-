"use client";
import { useEffect, useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Brand, Field, Notice } from "@/components/product/ui";
import { api, post, User } from "@/lib/api";
import { SignalField } from "@/components/product/signal-field";
import { ArrowUpRight, Eye, EyeSlash, ArrowLeft, Fingerprint, Code, Buildings } from "@phosphor-icons/react";

export function AuthView() {
  const params = useSearchParams();
  const [hydrated,setHydrated]=useState(false);
  useEffect(()=>setHydrated(true),[]);
  const router = useRouter();
  const [mode, setMode] = useState(params.get("mode") || "login");
  useEffect(() => { setMode(params.get("mode") || "login"); }, [params]);
  const [role, setRole] = useState(params.get("role") || "candidate");
  const [email, setEmail] = useState(params.get("email") || "");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState(params.get("deleted") === "1" ? "Аккаунт и связанные данные удалены" : "");
  const [demoLink, setDemoLink] = useState("");
  const [busy, setBusy] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [emailVerification, setEmailVerification] = useState(false);
  const [recovery, setRecovery] = useState(false);
  useEffect(() => {
    api<{ demo: boolean; email_verification: boolean; password_recovery: boolean }>("/health")
      .then((x) => { setIsDemo(x.demo); setEmailVerification(x.email_verification); setRecovery(x.password_recovery); })
      .catch(() => {});
  }, []);
  async function demo(which: string) {
    setBusy(true);
    setError("");
    try {
      await post<User>(`/auth/demo/${which}`);
      router.push("/app");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (mode === "verify") {
        await post<User>("/auth/verify", { token: params.get("token") });
        router.push("/app");
      } else if (mode === "reset") {
        const r = await post<{ message: string }>("/auth/reset", {
          token: params.get("token"),
          password,
        });
        setMessage(r.message);
        setMode("login");
      } else if (mode === "login") {
        await post<User>("/auth/login", { email, password });
        router.push("/app");
      } else {
        const r = await post<{ message: string; demo_link?: string; authenticated?: boolean }>(
          `/auth/${mode}`,
          mode === "register"
            ? { email, password, name, role, consent }
            : { email },
        );
        setMessage(r.message);
        setDemoLink(r.demo_link || "");
        if (r.authenticated) router.push("/app");
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const title =
    (
      {
        login: "С возвращением",
        register: "Создать аккаунт",
        verify: "Подтвердите почту",
        recover: "Восстановить доступ",
        resend: "Подтверждение почты",
        reset: "Новый пароль",
      } as Record<string, string>
    )[mode] || "Вход";
  return (
    <div className="rz-auth">
      <div className="rz-auth-story">
        <SignalField />
        <Brand />
        <div className="rz-auth-narrative">
          <p className="rz-auth-kicker"><Fingerprint size={22} /> Карьера с подтверждением</p>
          <h1>
            Ваш опыт.
            <br />
            <em>Новый разряд.</em>
          </h1>
          <p>
            Навыки становятся доказательствами.
            А доказательства открывают новые возможности.
          </p>
          <div className="rz-auth-proof">
            <span><b>01</b> Подтвердите уровень</span>
            <span><b>02</b> Получите предложение</span>
            <span><b>03</b> Выберите свою команду</span>
          </div>
        </div>
        <small>Спортивное программирование. Профессиональный рост.<span>ФСП × ЛЦТ 2026</span></small>
      </div>
      <main className="rz-auth-main">
        <Link href="/" className="rz-back">
          <ArrowLeft size={16} /> На главную
        </Link>
        <div className="rz-auth-card">
          <div className="rz-auth-form-brand"><Brand /></div>
          <h2>{title}</h2>
          <p className="rz-muted">
            {mode === "register"
              ? "Выберите роль и начните с короткого знакомства."
              : "Ваш профиль, результаты и предложения уже здесь."}
          </p>
          {error && <Notice error>{error}</Notice>}
          {message && <Notice>{message}</Notice>}
          {demoLink && (
            <Notice>
              Демонстрационная доставка письма:{" "}
              <Link href={demoLink}>открыть одноразовую ссылку</Link>. В рабочем
              окружении она приходит на почту.
            </Notice>
          )}
          <form onSubmit={submit} className="rz-form"><fieldset disabled={!hydrated} style={{display:"contents"}}>
            {mode === "register" && (
              <>
                <div className="rz-switch">
                  <button
                    type="button"
                    className={role === "candidate" ? "active" : ""}
                    onClick={() => setRole("candidate")}
                  >
                    Я специалист
                  </button>
                  <button
                    type="button"
                    className={role === "employer" ? "active" : ""}
                    onClick={() => setRole("employer")}
                  >
                    Я работодатель
                  </button>
                </div>
                <Field
                  label={
                    role === "candidate" ? "Ваше имя" : "Название компании"
                  }
                >
                  <input
                    required
                    minLength={2}
                    maxLength={120}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoComplete="name"
                  />
                </Field>
              </>
            )}
            {!["verify", "reset"].includes(mode) && (
              <Field label="Электронная почта">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </Field>
            )}
            {["login", "register", "reset"].includes(mode) && (
              <Field
                label="Пароль"
                hint={mode !== "login" ? "Не менее 10 символов" : ""}
              >
                <span className="rz-password"><input
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={mode === "login" ? 1 : 10}
                  maxLength={128}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                /><button type="button" aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeSlash size={20} /> : <Eye size={20} />}</button></span>
              </Field>
            )}
            {mode === "register" && (
              <label className="rz-check">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  required
                />
                <span>
                  Согласен на обработку данных по{" "}
                  <Link href="/privacy-policy">
                    политике конфиденциальности
                  </Link>
                  . Публикация профиля включается отдельно.
                </span>
              </label>
            )}
            <button disabled={busy} className="rz-button primary" type="submit">
              {busy
                ? "Подождите…"
                : mode === "login"
                  ? "Войти →"
                  : mode === "register"
                    ? "Создать аккаунт →"
                    : mode === "verify"
                      ? "Подтвердить и войти →"
                      : mode === "reset"
                        ? "Сохранить пароль"
                        : "Отправить письмо"}
            </button>
          </fieldset></form>
          <div className="rz-auth-links">
            {mode === "login" ? (
              <>
                <button onClick={() => setMode("register")}>
                  Создать аккаунт
                </button>
                {recovery && <button onClick={() => setMode("recover")}>
                  Забыли пароль?
                </button>}
                {emailVerification && <button onClick={() => setMode("resend")}>Нет письма?</button>}
              </>
            ) : (
              <button
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
              >
                Уже есть аккаунт? Войти
              </button>
            )}
          </div>
          {isDemo && (
            <div className="rz-demo">
              <span>Или познакомьтесь с платформой</span>
              <div>
                <button
                  className="rz-button"
                  disabled={busy}
                  onClick={() => demo("candidate")}
                  aria-label="Кабинет специалиста"
                >
                  <Code size={21} /><span>Специалист<small>Навыки и предложения</small></span><ArrowUpRight size={16} />
                </button>
                <button
                  className="rz-button"
                  disabled={busy}
                  onClick={() => demo("employer")}
                  aria-label="Кабинет работодателя"
                >
                  <Buildings size={21} /><span>Работодатель<small>Команда и подбор</small></span><ArrowUpRight size={16} />
                </button>
              </div>
              <small>Демонстрационные аккаунты и синтетические данные</small>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
