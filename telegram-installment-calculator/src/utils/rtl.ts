const RTL_ISOLATE = '\u2067';
const POP_DIRECTIONAL_ISOLATE = '\u2069';

export function rtl(text: string): string {
  return `${RTL_ISOLATE}${text}${POP_DIRECTIONAL_ISOLATE}`;
}

export function stripDirectionalIsolates(text: string): string {
  return text.replace(/[\u2066-\u2069]/g, '');
}
