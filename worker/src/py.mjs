/* Small helpers that reproduce the Python standard-library behaviour the demo
   API relies on (integer coercion, str/repr formatting, line splitting and
   timestamp formatting). Keeping them in one place makes the port auditable. */

/** Python's str.splitlines() for the LF-only files this demo writes. */
export function splitLines(text) {
  if (text === "") return [];
  const parts = text.split("\n");
  if (parts[parts.length - 1] === "") parts.pop();
  return parts;
}

/** Python str(value) for the scalar JSON types. */
export function pyStr(value) {
  if (value === null || value === undefined) return "None";
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "True" : "False";
  return String(value);
}

/** Python repr(value) for the scalar JSON types (used in error messages). */
export function pyRepr(value) {
  if (value === null || value === undefined) return "None";
  if (typeof value === "string") return `'${value.replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value === "number") return String(value);
  return JSON.stringify(value);
}

/**
 * Python int(value): truncates floats toward zero, parses ±digits strings,
 * treats booleans as 0/1 and rejects everything else.
 */
export function pyInt(value) {
  if (typeof value === "boolean") return value ? 1 : 0;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("cannot convert");
    return Math.trunc(value);
  }
  if (typeof value === "string") {
    const text = value.trim();
    if (/^[+-]?\d+$/.test(text)) return Number.parseInt(text, 10);
  }
  throw new TypeError("cannot convert");
}

/** Python json.dumps(...) with ensure_ascii for the fields we echo back. */
export function pyJsonString(value) {
  return JSON.stringify(value);
}

/** True when every code unit is ASCII, like str.isascii(). */
export function isAscii(text) {
  for (let index = 0; index < text.length; index += 1) {
    if (text.charCodeAt(index) > 0x7f) return false;
  }
  return true;
}

const ASCII_DIGITS = /^[0-9]+$/;

/** str.isdigit() restricted to ASCII digits (the only kind this demo emits). */
export function isDigit(text) {
  return text.length > 0 && ASCII_DIGITS.test(text);
}

/** ISO-8601 UTC with no fractional part, like datetime.replace("+00:00", "Z"). */
export function isoUtc(date) {
  return date.toISOString().replace(/\.\d{3}Z$/, "Z");
}

/**
 * ISO-8601 UTC with six fractional digits (Python's isoformat for a datetime
 * that has a microsecond component). JS Date only resolves milliseconds, so the
 * last three digits are always "000".
 */
export function isoUtcMicros(date) {
  const iso = date.toISOString();
  return `${iso.slice(0, -1)}000Z`;
}

/** Python round(value, digits), used for the timing fields. */
export function roundTo(value, digits) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

/** Integer bit length, matching int.bit_length(). */
export function bitLength(value) {
  let n = value < 0 ? -value : value;
  let bits = 0;
  while (n > 0) {
    bits += 1;
    n = Math.floor(n / 2);
  }
  return bits;
}
