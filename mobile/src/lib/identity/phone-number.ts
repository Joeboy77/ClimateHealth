const VALID_PREFIXES = [
  "024",
  "054",
  "055",
  "059",
  "025",
  "053",
  "020",
  "050",
  "027",
  "057",
  "026",
  "056",
];

export const LOCAL_NUMBER_LENGTH = 10;
export const MINIMUM_PASSWORD_LENGTH = 6;

/**
 * A Ghanaian number in the 0XXXXXXXXX form the backend stores.
 *
 * People type their number every way there is: with the country code, with a plus, with
 * spaces from a contact card. The server accepts all of them, and so does this, so the
 * Continue button never goes dead on somebody who typed a perfectly good number.
 */
export function asLocalNumber(entered: string): string {
  const digits = entered.replace(/\D/g, "");
  const withoutCountryCode = digits.startsWith("233")
    ? digits.slice(3)
    : digits.startsWith("00233")
      ? digits.slice(5)
      : digits;
  return withoutCountryCode.startsWith("0")
    ? withoutCountryCode
    : `0${withoutCountryCode}`;
}

export function isCompleteNumber(entered: string): boolean {
  const local = asLocalNumber(entered);
  return (
    local.length === LOCAL_NUMBER_LENGTH && VALID_PREFIXES.includes(local.slice(0, 3))
  );
}
