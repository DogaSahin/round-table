import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Modal from './Modal.vue'

describe('Modal', () => {
  it('renders default, header, and footer slot content', () => {
    const wrapper = mount(Modal, {
      slots: {
        default: '<p>Body</p>',
        header: '<h2>Title</h2>',
        footer: '<button>Save</button>',
      },
    })

    expect(wrapper.html()).toContain('<p>Body</p>')
    expect(wrapper.html()).toContain('<h2>Title</h2>')
    expect(wrapper.html()).toContain('<button>Save</button>')
  })

  it('omits the header and footer wrapper elements when those slots are not used', () => {
    const wrapper = mount(Modal, { slots: { default: '<p>Body</p>' } })

    expect(wrapper.find('.modal__header').exists()).toBe(false)
    expect(wrapper.find('.modal__footer').exists()).toBe(false)
  })

  it('emits close on a backdrop click but not a click inside the body', async () => {
    const wrapper = mount(Modal, { slots: { default: '<p>Body</p>' } })

    await wrapper.find('.modal__body').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()

    await wrapper.find('.modal__backdrop').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close on Escape keydown', async () => {
    const wrapper = mount(Modal, { slots: { default: '<p>Body</p>' } })

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(wrapper.emitted('close')).toHaveLength(1)
  })
})
