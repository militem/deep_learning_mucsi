# 🛂 Papers, Please - IA Multiagente (Ollama Edition)

Este proyecto es una simulación basada en el videojuego *Papers, Please*, construida con una arquitectura de **Sistemas Multiagente**.

Utiliza **Modelos de Lenguaje Grande (LLMs)** ejecutados de forma local (mediante **Ollama**) para simular la interacción entre un **Inspector de Aduanas** y los **Solicitantes/Ciudadanos**.

---

## 📁 Estructura del Proyecto

El código está diseñado de forma modular siguiendo los principios de responsabilidad única (**SOLID**):

* **`config.py`**
  Contiene la configuración global del proyecto (URL de Ollama, nombre del modelo, créditos iniciales, etc.).

* **`generator.py`**
  Motor de generación procedimental. Crea la *Verdad Fundamental* (**Ground Truth**) de cada ciudadano, sus documentos en formato JSON y decide si intentan pasar con documentos falsos o caducados.

* **`agents.py`**
  Define la clase `AgenteLLM`. Es un wrapper agnóstico que gestiona el historial de conversación y realiza llamadas a la API local de Ollama usando la interfaz estándar de OpenAI.

* **`engine.py`**
  Contiene la clase `MotorPapersPlease`. Es el núcleo lógico del juego:

  * Gestiona turnos
  * Enfrenta a los agentes
  * Aplica reglas del día
  * Evalúa decisiones del inspector (multas o créditos)

* **`main.py`**
  Punto de entrada de la aplicación. Configura el cliente local e inicia el bucle de juego.

---

## 🚀 Requisitos Previos e Instalación

Para ejecutar este proyecto necesitas:

* Python **3.8+**
* **Ollama** instalado

---

### 1. Instalar Ollama (Motor LLM Local)

Ollama permite ejecutar modelos de lenguaje en local de forma privada.

* **Windows / macOS:**
  Descargar desde 👉 [https://ollama.com](https://ollama.com)

* **Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

### 2. Descargar el Modelo

Por defecto, el proyecto usa el modelo **llama3**.

Ejecuta:

```bash
ollama run llama3
```

> ⚠️ Nota:
> La primera vez tardará unos minutos en descargar el modelo.
> Cuando veas el prompt de Ollama, el servidor ya estará activo en el puerto `11434`.

---

### 3. Preparar el Entorno de Python

Clona o descarga el proyecto y, desde la raíz, ejecuta:

```bash
pip install -r requirements.txt
```

---

## 🕹️ Cómo Jugar / Ejecutar la Simulación

Asegúrate de que el servidor de Ollama está corriendo en segundo plano.

Luego ejecuta:

```bash
python main.py
```

---

## 🎮 Qué Ocurre Durante la Ejecución

En la consola podrás ver:

* Generación de ciudadanos
* Creación de documentos en JSON
* Análisis por parte del inspector
* Interacción entre agentes
* Decisión final estructurada

---

## 🏁 Resultado

El sistema evalúa si la decisión del inspector es correcta y:

* ✅ Otorga créditos
* ❌ Aplica multas

---

## ✨ Nota Final

¡Gloria a Arstotzka!
