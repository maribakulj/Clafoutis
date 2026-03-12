declare module 'mirador' {
  const mirador: {
    viewer: (config: unknown, container: HTMLElement) => {
      store?: {
        getState: () => unknown
        subscribe: (listener: () => void) => () => void
      }
    }
  }

  export default mirador
}
