import type { ReactNode } from "react";

export function ScrollableTable({
  caption,
  children,
  className,
  tableClassName,
}: {
  caption: string;
  children: ReactNode;
  className?: string;
  tableClassName?: string;
}) {
  const regionClassName = className ? `table-scroll ${className}` : "table-scroll";

  return (
    <div className={regionClassName} role="region" tabIndex={0} aria-label={caption}>
      <table className={tableClassName}>
        <caption>{caption}</caption>
        {children}
      </table>
    </div>
  );
}
