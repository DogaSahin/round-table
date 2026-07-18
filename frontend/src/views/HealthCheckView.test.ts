import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import HealthCheckView from './HealthCheckView.vue'
import * as client from '@/api/client'

describe('HealthCheckView', () => {
  it('renders the status once the health check resolves', async () => {
    vi.spyOn(client, 'apiFetch').mockResolvedValue({ status: 'ok' })

    const wrapper = mount(HealthCheckView)
    await flushPromises()

    expect(wrapper.text()).toContain('ok')
    expect(client.apiFetch).toHaveBeenCalledWith('/health')
  })

  it('renders an error message if the health check fails', async () => {
    vi.spyOn(client, 'apiFetch').mockRejectedValue(
      new client.ApiError('internal_error', 'Something broke', {}, 500),
    )

    const wrapper = mount(HealthCheckView)
    await flushPromises()

    expect(wrapper.text()).toContain('Something broke')
  })
})
