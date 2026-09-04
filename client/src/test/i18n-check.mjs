/**
 * Dictionary parity check.
 *
 * A Hindi key with no English counterpart silently falls back to Hindi when the
 * user toggles to English, which looks like a broken toggle rather than a
 * missing string. This makes that loud.
 */
import dict from "../lib/i18n.js";

const hi = Object.keys(dict.hi);
const en = Object.keys(dict.en);
const missingEn = hi.filter((k) => !en.includes(k));
const missingHi = en.filter((k) => !hi.includes(k));

console.log(`hi keys: ${hi.length}  en keys: ${en.length}`);
console.log(`missing English: ${missingEn.length}`, missingEn.slice(0, 8));
console.log(`missing Hindi:   ${missingHi.length}`, missingHi.slice(0, 8));

if (missingEn.length || missingHi.length) process.exit(1);
console.log("dictionaries are in parity");
