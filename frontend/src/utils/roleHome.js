// Where each role lands after signing in.
export const ROLE_HOME = {
  super_admin: '/super-admin',
  admin: '/admin',
  teacher: '/teacher',
  student: '/student',
};

/**
 * Turns an axios error into a readable message. FastAPI returns `detail`
 * as a string for most errors, but as a list of {msg, loc} objects for
 * validation errors (422).
 */
export function apiErrorMessage(err, fallback = 'Something went wrong. Please try again.') {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => (typeof d?.msg === 'string' ? d.msg.replace(/^Value error, /, '') : null))
      .filter(Boolean)
      .join('. ') || fallback;
  }
  return fallback;
}
