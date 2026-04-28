"use strict";
Component({
    properties: {
        show: { type: Boolean, value: false },
        result: { type: Object, value: null },
        state: { type: Object, value: {} },
        ended: { type: Boolean, value: false },
        ending: { type: Object, value: null },
    },
    methods: {
        onClose() {
            if (!this.data.ended) {
                this.triggerEvent('close');
            }
        },
        onRestart() {
            this.triggerEvent('restart');
        },
        onHome() {
            this.triggerEvent('home');
        },
        deltaClass(val) {
            return val > 0 ? 'delta-positive' : val < 0 ? 'delta-negative' : 'delta-zero';
        },
    },
});
