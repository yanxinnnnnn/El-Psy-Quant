import { NextIntlClientProvider } from "next-intl";
import type { ReactElement, ReactNode } from "react";
import {
  render as testingLibraryRender,
  type RenderOptions as TestingLibraryRenderOptions,
} from "@testing-library/react";

import { DEFAULT_LOCALE, type Locale } from "@/i18n/config";
import { loadMessages } from "@/i18n/messages";

type RenderOptions = Omit<TestingLibraryRenderOptions, "wrapper"> & {
  locale?: Locale;
};

export * from "@testing-library/react";

export function render(ui: ReactElement, options: RenderOptions = {}) {
  const { locale = DEFAULT_LOCALE, ...renderOptions } = options;
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NextIntlClientProvider locale={locale} messages={loadMessages(locale)}>
        {children}
      </NextIntlClientProvider>
    );
  }
  return testingLibraryRender(ui, { wrapper: Wrapper, ...renderOptions });
}
