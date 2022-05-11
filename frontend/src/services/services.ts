export const fetchPopulationData = () => {
  return fetch('http://localhost:5000/api/scenario/languages', {mode: 'cors'})
  .then(async (data) => {
    const JSONData = await data.json()
    return JSONData
  })
}