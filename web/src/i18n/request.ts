import { getRequestConfig } from "next-intl/server";

import { resolveRequestLocale } from "@/i18n/locale";
import { loadMessages } from "@/i18n/messages";

export default getRequestConfig(async () => {
  const locale = await resolveRequestLocale();
  return {
    locale,
    messages: loadMessages(locale),
  };
});
