let gameStatusComponent = {
    components: {
        'probability-bar-component': probabilityBarComponent,
        'grain-image-component': grainImageComponent,
    },
    props: {
        civiliansPerGroup: Number,
        balance: Number,
        balanceColor: String,
        stealNotification: String,
        interceptCount: Number,
        arrestsCount: Number,
        falseArrestCount: Number,
        investigationCount: Number,
        defendTokenTotal: Number,
        isOfficer: Boolean,
        aMax: Number,
        beta: Number,
        reviewProbability: Number,
    },
    data: function () {
        return {
        }
    },
    mounted: function () {

    },
    methods: {
        randomLocation: function () {
            return null
        }
    },
    computed: {
        probabilityCulprit() {
            if (this.investigationCount > this.aMax)
                return this.beta * 100;
            else {
                let guilty = this.beta * (1/(this.civiliansPerGroup - 1) + ((this.civiliansPerGroup - 2) / (this.civiliansPerGroup - 1) * (this.investigationCount/this.aMax)))
                return Math.round(guilty*10000) / 100
            }
        },
        probabilityInnocent() {
            if (this.investigationCount > this.aMax)
                return 0;
            else {
                let innocent = this.beta * ((1/(this.civiliansPerGroup -1) - (1/(this.civiliansPerGroup -1)) * (this.investigationCount/this.aMax)))

                // calculate probability of officer reprimand because it depends on probability innocent
                if (this.isOfficer) {
                    let probabilityReprimand = Math.round(this.reviewProbability * 3 * innocent * 10000) / 100
                    this.$emit('update-probability-reprimand', probabilityReprimand)
                }

                return Math.round(innocent*10000) / 100
            }
        },
        // probabilityReprimand() {
        //     return Math.round(this.reviewProbability * 3 * this.probabilityInnocent); // todo: make this dynamic
        // }
    },
    template:
        `
            <div class="game-status-container">
                <div class="balance-container">
                    <div class="balance-label">Balance (<grain-image-component :size=20></grain-image-component>)</div>
                    <div class="balance" :style="{ color: balanceColor }"> {{Math.floor(balance)}}</div>
            
                    <div class="notification-label">
                        <div class="steal-notification">{{stealNotification}}</div>
                    </div>
            
                    <div class="count-container">
                        <div class="title-small data-row">
                            <div class="left"># Intercepts: </div>
                            <div class="right"><strong>{{ interceptCount }}</strong></div>
                        </div>
                        <div style="clear: both"></div>
                        <div class="title-small data-row">
                            <div class="left"># Fines: </div>
                            <div class="right"><strong>{{ arrestsCount }}</strong></div>
                        </div>
                        <div style="clear: both"></div>
                        <div class="title-small data-row">
                            <div class="left"># Reprimands: </div>
                            <div class="right"><strong>{{ falseArrestCount }}</strong></div>
                        </div>
                    </div>
                    <br>
                    <br>
                </div>
                <div class="probability-container">
                    <br>
                    <br>
                    <div class="title-small">Officer tokens on investigate: <strong>{{investigationCount}}/{{defendTokenTotal}}</strong></div>
                    <br>
                    <probability-bar-component
                            :label="isOfficer ? 'Probability you fine an innocent' : 'Probability fined if you are innocent'"
                            :percent="isOfficer ? probabilityInnocent * 3 : probabilityInnocent">
                    </probability-bar-component>
                    <br>
                    <probability-bar-component
                            :label="isOfficer ? 'Probability you fine the culprit' : 'Probability fined if you are the culprit'"
                            :percent=probabilityCulprit
                    ></probability-bar-component>
                </div>
            </div>
        `

}