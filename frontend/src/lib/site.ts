import { getServerEnv, publicEnv } from "@/env";
const production=getServerEnv().VERCEL_PROJECT_PRODUCTION_URL;
export const siteConfig={
 name:"Разряд",title:"Разряд — навыки говорят за вас",titleTemplate:"%s — Разряд",
 description:"Подтвердите навыки и получайте предложения от ИТ-команд. Проверенный грейд, достижения ФСП и контакты под вашим контролем.",
 url:publicEnv.NEXT_PUBLIC_SITE_URL??(production?`https://${production}`:"http://localhost:3000"),
 ogImage:"/brand.svg",ogImageAlt:"Разряд — навыки говорят за вас",twitterHandle:undefined as string|undefined,
 author:"Разряд",keywords:["ИТ-вакансии","спортивное программирование","ФСП","подтверждение навыков","обратный найм","ЛЦТ 2026"],themeColor:"#090a0d",
} as const;
