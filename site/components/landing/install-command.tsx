"use client";

import { useEffect, useRef, useState } from "react";
import { INSTALL_COMMAND } from "@/lib/release";

/**
 * InstallCommand — hero CTA chip with one-click copy.
 * Mirrors the pattern used across heartland-protocol sibling sites.
 */
export function InstallCommand() {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);
  const [pending, setPending] = useState(false);
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (resetTimer.current) clearTimeout(resetTimer.current);
  }, []);

  async function handleCopy() {
    setPending(true);
    setCopied(false);
    setFailed(false);
    if (resetTimer.current) clearTimeout(resetTimer.current);
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(INSTALL_COMMAND);
      setCopied(true);
      resetTimer.current = setTimeout(() => setCopied(false), 1600);
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="max-w-full">
      <code className="mb-3 block break-all font-mono text-[14.5px] leading-relaxed text-cool">{INSTALL_COMMAND}</code>
      <button
        type="button"
        onClick={handleCopy}
        disabled={pending}
        aria-label="Copy install command"
        className="inline-flex max-w-full items-center rounded-full border border-grid bg-panel px-5 py-3 text-left font-editorial text-sm text-cool transition-colors hover:border-cool/40 disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-alert"
      >
        {copied ? "Copied" : pending ? "Copying" : "Copy command"}
      </button>
      <p role="status" className="mt-2 min-h-5 text-sm text-cool/75">
        {failed ? "Copy unavailable. Select the command above and copy it manually." : copied ? "Command copied." : ""}
      </p>
    </div>
  );
}
