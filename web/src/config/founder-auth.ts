export const FOUNDER_USERNAME_ENV = "EL_PSY_QUANT_FOUNDER_USERNAME";
export const FOUNDER_PASSWORD_ENV = "EL_PSY_QUANT_FOUNDER_PASSWORD";
export const FOUNDER_AUTH_REALM = "El-Psy-Quant Founder";

const MAX_CREDENTIAL_LENGTH = 128;
const MAX_AUTHORIZATION_LENGTH = 512;

export type FounderAuthConfig = Readonly<{
  username: string;
  password: string;
}>;

function validateCredential(
  value: string,
  name: string,
  allowColon: boolean,
): string {
  if (value.length === 0) {
    throw new Error(`${name} must be a non-empty string`);
  }
  if (value.length > MAX_CREDENTIAL_LENGTH) {
    throw new Error(`${name} must be at most ${MAX_CREDENTIAL_LENGTH} characters`);
  }
  for (const character of value) {
    const code = character.charCodeAt(0);
    if (code < 33 || code > 126) {
      throw new Error(`${name} must use visible ASCII characters`);
    }
  }
  if (!allowColon && value.includes(":")) {
    throw new Error(`${name} must not contain a colon`);
  }
  return value;
}

export function resolveFounderAuthConfig(
  username: string | undefined,
  password: string | undefined,
): FounderAuthConfig | null {
  if (username === undefined && password === undefined) {
    return null;
  }
  if (username === undefined || password === undefined) {
    throw new Error(
      `${FOUNDER_USERNAME_ENV} and ${FOUNDER_PASSWORD_ENV} must be configured together`,
    );
  }
  return {
    username: validateCredential(username, FOUNDER_USERNAME_ENV, false),
    password: validateCredential(password, FOUNDER_PASSWORD_ENV, true),
  };
}

export function founderAuthorizationValue(config: FounderAuthConfig): string {
  return `Basic ${btoa(`${config.username}:${config.password}`)}`;
}

export function authorizationMatchesFounder(
  authorization: string | null,
  config: FounderAuthConfig,
): boolean {
  if (authorization === null) {
    return false;
  }
  const expected = founderAuthorizationValue(config);
  let difference = authorization.length ^ expected.length;
  for (let index = 0; index < MAX_AUTHORIZATION_LENGTH; index += 1) {
    difference |=
      (authorization.charCodeAt(index) || 0) ^ (expected.charCodeAt(index) || 0);
  }
  return authorization.length <= MAX_AUTHORIZATION_LENGTH && difference === 0;
}
