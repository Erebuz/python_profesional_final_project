export const requirement = (val: string) =>
  val.length > 0 || 'Обязательное поле'
export const max60 = (val: string) => val.length < 60 || 'Не более 60 символов'
