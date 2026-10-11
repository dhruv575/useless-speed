import { useEffect, useId, useRef, useState } from "react";
import { MapPin, Search, Circle, Navigation } from "lucide-react";
import type { Place } from "./model/types";

// The city directory supplies all-caps addresses. Never capitalize user text;
// soften only those source labels instead of presenting them in all caps.
const displayCase = (text: string) =>
  text === text.toLocaleUpperCase() ? text.toLocaleLowerCase() : text;
export default function AddressInput({
  label,
  letter,
  place,
  onChange,
  onPin,
  pinning,
}: {
  label: string;
  letter: string;
  place: Place | null;
  onChange: (p: Place | null) => void;
  onPin: () => void;
  pinning: boolean;
}) {
  const id = useId(),
    [query, setQuery] = useState(place?.label || ""),
    [items, setItems] = useState<Place[]>([]),
    [open, setOpen] = useState(false),
    [active, setActive] = useState(-1),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (place) {
      setQuery(place.label);
      setOpen(false);
    }
  }, [place]);
  useEffect(() => {
    if (!open || query.length < 2) {
      setItems([]);
      setBusy(false);
      setActive(-1);
      return;
    }
    const controller = new AbortController();
    setBusy(true);
    setItems([]);
    setActive(-1);
    setError("");
    const timeout = setTimeout(async () => {
      try {
        const r = await fetch("/api/search?q=" + encodeURIComponent(query), {
          signal: controller.signal,
        });
        if (!r.ok) throw Error();
        const results: Place[] = await r.json();
        setItems(
          results.map((p) => ({
            ...p,
            label: displayCase(p.label),
            landmark: p.landmark ? displayCase(p.landmark) : p.landmark,
            address: p.address ? displayCase(p.address) : p.address,
          })),
        );
        setActive(-1);
      } catch (e) {
        if (!controller.signal.aborted)
          setError("Search unavailable. You can still drop a pin.");
      } finally {
        if (!controller.signal.aborted) setBusy(false);
      }
    }, 220);
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [query, open]);
  function choose(p: Place) {
    onChange(p);
    setQuery(p.label);
    setOpen(false);
    input.current?.blur();
  }
  return (
    <div className="address-field">
      <label className="sr-only" htmlFor={id}>
        {label}
      </label>
      <div className={"address-box " + (pinning ? "is-pinning" : "")}>
        <span
          className={"address-icon " + letter.toLowerCase()}
          aria-hidden="true"
        >
          {letter === "A" ? <Circle size={15} /> : <Navigation size={16} />}
        </span>
        <input
          ref={input}
          id={id}
          value={query}
          placeholder={label}
          title="Search a place or street address in San Francisco"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={id + "-list"}
          aria-activedescendant={active >= 0 ? id + "-" + active : undefined}
          autoComplete="off"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          onFocus={() => {
            if (!place) setOpen(true);
          }}
          onChange={(e) => {
            const v = e.target.value;
            setQuery(v);
            setOpen(true);
            if (place) onChange(null);
          }}
          onBlur={() => setOpen(false)}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setOpen(false);
              input.current?.blur();
            }
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setOpen(true);
              setActive(Math.min(items.length - 1, active + 1));
            }
            if (e.key === "ArrowUp" && items.length) {
              e.preventDefault();
              setActive(Math.max(0, active - 1));
            }
            if (e.key === "Enter" && open && !busy && items.length) {
              e.preventDefault();
              choose(items[Math.max(0, active)]);
            }
          }}
        />
        <button
          type="button"
          className={"pin-button " + (pinning ? "selected" : "")}
          onClick={onPin}
          aria-label={"Drop " + label.toLowerCase() + " pin"}
          aria-pressed={pinning}
          title={"Choose " + label.toLowerCase() + " on map"}
        >
          <MapPin size={17} />
        </button>
      </div>
      {open && query.length >= 2 && (
        <div
          className="search-results"
          id={id + "-list"}
          role="listbox"
          aria-label={label + " suggestions"}
        >
          {busy ? (
            <div className="search-message">
              Searching places and addresses…
            </div>
          ) : error ? (
            <div className="search-message">{error}</div>
          ) : items.length ? (
            items.map((p, i) => (
              <button
                key={p.id}
                id={id + "-" + i}
                role="option"
                aria-selected={active === i}
                className={active === i ? "active" : ""}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(p)}
              >
                {p.kind === "address" ? (
                  <Search size={14} />
                ) : (
                  <MapPin size={14} />
                )}
                <span>
                  <strong>{p.label}</strong>
                  <small>
                    {p.address ||
                      p.category ||
                      p.neighborhood ||
                      "San Francisco"}
                  </small>
                </span>
              </button>
            ))
          ) : (
            <div className="search-message">
              No matching place or address. Try another name, or drop a pin.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
