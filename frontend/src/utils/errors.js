/**
 * Formats API network and response errors into clear, human-readable strings.
 */
export function formatApiError(err, fallbackMessage = 'An unexpected error occurred. Please try again.') {
  if (!err) return fallbackMessage

  // 1. Network / Server Unreachable Error
  if (!err.response) {
    if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
      return 'Unable to connect to BudgetBuddy server. Please check your internet connection or try again later.'
    }
    return err.message || fallbackMessage
  }

  const { status, data } = err.response

  // 2. HTTP Status specific messages
  if (status === 500) {
    if (data && typeof data === 'object' && data.detail) {
      return data.detail
    }
    return 'Internal server error encountered. Please try again later.'
  }
  if (status === 502 || status === 503 || status === 504) {
    return 'BudgetBuddy service is temporarily unavailable. Please try again shortly.'
  }

  // 3. String responses
  if (typeof data === 'string') {
    return data.length < 200 ? data : fallbackMessage
  }

  // 4. Object response handling (Django REST Framework errors)
  if (data && typeof data === 'object') {
    if (data.detail && typeof data.detail === 'string') {
      return data.detail
    }

    if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
      return data.non_field_errors.join(' ')
    }

    // Collect all field validation errors: { title: ["Title is required"], amount: ["Enter a number"] }
    const fieldErrors = []
    for (const [field, msgs] of Object.entries(data)) {
      if (Array.isArray(msgs)) {
        const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace('_', ' ')
        fieldErrors.push(`${fieldName}: ${msgs.join(' ')}`)
      } else if (typeof msgs === 'string') {
        fieldErrors.push(msgs)
      }
    }

    if (fieldErrors.length > 0) {
      return fieldErrors.join(' | ')
    }
  }

  return fallbackMessage
}
