/** @odoo-module **/

import { Component, useState, markup, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AiAssistantSystray extends Component {
    setup() {
        this.state = useState({
            isOpen: false,
            messages: [],
            currentInput: "",
            isLoading: false,
            isListening: false, 
            x: window.innerWidth - 380,
            y: 60,
            isDragging: false,
            sessionTokens: 0,
            hasAccess: false
        });

        this.userService = useService("user");
        this.rpc = useService("rpc");
        this.actionService = useService("action");

        onWillStart(async () => {
            try {
                this.state.hasAccess = await this.userService.hasGroup('ai_user_assistant.group_ai_assistant_user');
                console.log("🎩 Asistente IA - ¿Tiene permiso el usuario actual?", this.state.hasAccess);
            } catch (error) {
                console.error("❌ Asistente IA - Error verificando el permiso:", error);
            }
        });
        
        this.sendMessage = this.sendMessage.bind(this);
        this.toggleChat = this.toggleChat.bind(this);
        this.toggleVoiceRecognition = this.toggleVoiceRecognition.bind(this); 
        
        this.onDragStart = this.onDragStart.bind(this);
        this.onDrag = this.onDrag.bind(this);
        this.onDragEnd = this.onDragEnd.bind(this);
        
        this.recognition = null;
    }

    toggleVoiceRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            alert("Tu navegador no soporta búsqueda por voz nativa. Intenta usar Google Chrome o Edge.");
            return;
        }

        if (this.state.isListening && this.recognition) {
            this.recognition.stop();
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'es-ES'; 
        this.recognition.continuous = false;
        this.recognition.interimResults = false;

        this.recognition.onstart = () => {
            this.state.isListening = true;
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            
            if (this.state.currentInput.trim()) {
                this.state.currentInput += " " + transcript;
            } else {
                this.state.currentInput = transcript;
            }
        };

        this.recognition.onerror = (event) => {
            console.error("Error en el reconocimiento de voz:", event.error);
            if (event.error === 'not-allowed') {
                alert("Has bloqueado el acceso al micrófono. Por favor, haz clic en el icono del candado en la barra de direcciones de Chrome y permite el uso del micrófono.");
            }
            this.state.isListening = false;
        };

        this.recognition.onspeechend = () => {
            this.recognition.stop();
        };

        this.recognition.onend = () => {
            this.state.isListening = false;
        };

        this.recognition.start();
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    onDragStart(ev) {
        this.state.isDragging = true;
        this.dragStartX = ev.clientX - this.state.x;
        this.dragStartY = ev.clientY - this.state.y;
        document.addEventListener('mousemove', this.onDrag);
        document.addEventListener('mouseup', this.onDragEnd);
    }

    onDrag(ev) {
        if (!this.state.isDragging) return;
        this.state.x = ev.clientX - this.dragStartX;
        this.state.y = ev.clientY - this.dragStartY;
    }

    onDragEnd() {
        this.state.isDragging = false;
        document.removeEventListener('mousemove', this.onDrag);
        document.removeEventListener('mouseup', this.onDragEnd);
    }

    get windowStyle() {
        return `position: fixed; top: ${this.state.y}px; left: ${this.state.x}px; margin: 0; z-index: 9999; width: 350px;`;
    }

    async sendMessage() {
        if (!this.state.currentInput.trim() || this.state.isLoading) return;

        const userMessage = this.state.currentInput;
        this.state.messages.push({ role: "user", content: userMessage });
        this.state.currentInput = "";
        this.state.isLoading = true;

        let contextData = { active_model: "Desconocido", view_type: "Desconocido", fields_info: [] };
        
        try {
            let isDashboard = false;
            
            // 1. EL LÁSER (Funciona perfectamente gracias a tus logs)
            const x = window.innerWidth / 2;
            const y = window.innerHeight / 2;
            const topElement = document.elementFromPoint(x, y);

            if (topElement) {
                const isMenuElement = topElement.closest('.o_home_menu') || 
                                      topElement.closest('.o_app') || 
                                      topElement.closest('.o_menu_apps') ||
                                      topElement.classList.contains('o_home_menu_background') ||
                                      topElement.tagName === 'BODY'; 
                
                if (isMenuElement) {
                    isDashboard = true;
                }
            }

            // 2. EL BUG ESTABA AQUÍ (Corregido: Si la URL tiene 'model=', sabemos que NO es el Dashboard)
            const hashStr = window.location.hash;
            if (!hashStr || hashStr === '#' || hashStr === '#home' || 
                (hashStr.includes('menu_id') && !hashStr.includes('action=') && !hashStr.includes('model='))) {
                isDashboard = true;
            }

            console.log("🔍 [DEBUG] URL actual:", hashStr);
            console.log("🔍 [DEBUG] Elemento tocado por el láser:", topElement);

            // --- ASIGNACIÓN FINAL ---
            if (isDashboard) {
                contextData.active_model = "Dashboard Principal (Menú de Inicio)";
                contextData.view_type = "Menú";
                contextData.fields_info = []; // Vaciamos los campos
            } else {
                const currentController = this.actionService.currentController;
                if (currentController && currentController.action) {
                    contextData.active_model = currentController.action.res_model || "Desconocido";
                    contextData.view_type = currentController.view?.type || "Desconocido";
                }

                const domElements = Array.from(document.querySelectorAll('.o_form_label, thead th'));
                const visibleLabels = domElements
                    .filter(el => el.offsetWidth > 0 && el.offsetHeight > 0) 
                    .map(el => el.innerText.trim())
                    .filter(text => text.length > 0 && text !== '​');

                if (visibleLabels.length > 0) {
                    contextData.fields_info = [...new Set(visibleLabels)].slice(0, 30);
                }
            }
        } catch (e) { 
            console.error("Error capturando contexto visual:", e);
        }

        console.log("📤 Modelo detectado:", contextData.active_model);
        console.log("📤 Campos leídos de la pantalla:", contextData.fields_info);

        try {
            const response = await this.rpc("/ai_assistant/ask", {
                question: userMessage,
                context_data: contextData
            });

            if (response.status === "success") {
                this.state.messages.push({ role: "assistant", content: markup(response.answer) });
                if (response.tokens) {
                    this.state.sessionTokens += response.tokens;
                }
                
               // --- AÑADE ESTE BLOQUE PARA LA NAVEGACIÓN ---
                if (response.action) {
                    console.log("🚀 Ejecutando acción de navegación:", response.action);
                    
                    let action = response.action;
                    
                    // Saneamos la acción para que el frontend de Odoo no explote
                    if (action.type === 'ir.actions.act_window') {
                        // 1. Asegurar el dominio
                        if (!action.domain) {
                            action.domain = [];
                        }
                        
                        // 2. Odoo JS necesita 'views' en formato array, y usar 'list' en vez de 'tree'
                        if (!action.views) {
                            let viewMode = action.view_mode || 'list,form';
                            viewMode = viewMode.replace('tree', 'list'); // JS de Odoo 16 usa 'list'
                            action.views = viewMode.split(',').map(mode => [false, mode.trim()]);
                        }
                        
                        // 3. Asegurar el target
                        if (!action.target) {
                            action.target = 'current';
                        }
                    }

                    await this.actionService.doAction(action);
                }
                // --------------------------------------------

            } else {
                this.state.messages.push({ role: "assistant", content: markup(response.message) });
            }
        } finally {
            this.state.isLoading = false;
        }
    }
}

AiAssistantSystray.template = "ai_user_assistant.SystrayIcon";
registry.category("systray").add("ai_user_assistant.SystrayItem", { Component: AiAssistantSystray }, { sequence: 100 });