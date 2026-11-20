import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || (import.meta.env.PROD
	? 'https://attendpay-api-jjkz.onrender.com/api'
	: 'http://127.0.0.1:8000/api')

export const api = axios.create({ baseURL })
