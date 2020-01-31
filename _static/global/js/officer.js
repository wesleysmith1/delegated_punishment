let policeLogComponent = {
    props: {messages: Array,},
    watch: {
      	messages: function(newVal, oldVal) {
      	    this.$nextTick(() => {
                this.scrollToBottom()
            })
        }
    },
    data: function () {
        return {}
    },
    methods: {
        scrollToBottom: function() {
            let scrollHeight = this.$refs.policeLog1.scrollHeight

            this.$refs.policeLog1.scrollTop = scrollHeight;
            this.$refs.policeLog2.scrollTop = scrollHeight;
            this.$refs.policeLog3.scrollTop = scrollHeight;
        }
    },
    template:
        `
        <div class="police-log-container">
            <div class="title">Police Log</div>
            <div class="notification-log-container">
                <div class="notification-log-column">
                    <div class="header"><div>Civ Punished</div></div>
                    <div class="content" ref="policeLog1">
                        <div v-for="message in messages">{{message.civilianPunished}}</div>
                    </div>
                </div>
                <div class="notification-log-column">
                    <div class="header"><div>Map Number</div></div>
                    <div class="content" ref="policeLog2">
                        <div v-for="message in messages">{{message.mapNumber}}</div>
                    </div>
                </div>
                <div class="notification-log-column">
                    <div class="header"><div>Time (seconds)</div></div>
                    <div class="content" ref="policeLog3">
                        <div v-for="message in messages">{{message.time}}</div>
                    </div>
                </div>
            </div>

            <!--<button @click="addMessage">add message</button>-->
        </div>
        `
}

let probabilityBarComponent = {
    props: {
        label: String,
        percent: Number,
    },
    data: function () {
        return {}
    },
    template:
        `
        <div>
            {{ label }} {{percent}}%
            <div class='bar'>
                <div class="innocent" :style="{'width':(percent+'%')}">
                </div>
            </div>
        </div>
        `
}

let officerGameComponent = {
    components: {
        'probability-bar-component': probabilityBarComponent,
        'police-log-component': policeLogComponent,
    },
    props: {
        properties: Array,
        officerUnits: Array,
        playerGroupId: String,
        investigationCount: Number,
        probCulprit: Number,
        probInnocent: Number,
        policeLogMessages: Array,
        mapSize: Number,
        defendTokenSize: Number,
    },
    data: function () {
        return {
            playerId: Number,
            locationx: String,
            locationy: String,
            property: String,
        }
    },
    created: function () {
        this.locationx = '';
        this.locationy = '';
        this.property = '';
    },
    mounted: function () {
        for (let i = 0; i < this.officerUnits.length; i++) {
            let oGame = document.getElementById("officerGame");
            let that = this;
            let drag = Draggable.create("#unit" + i, {
                minimumMovement: .01,
                zIndexBoost: false, // todo: do we need this?
                bounds: document.getElementById("officerGame"), //todo add ref stuff
                onDragStart: function () {
                    that.tokenDragStart(this, that.officerUnits[i])
                },
                onDragEnd: function () {
                    that.checkLocation(this, that.officerUnits[i])
                },
            });
            drag.zIndex = 500;
        }
    },
    methods: {
        tokenDragStart: function (that, item) {
            // console.log(item)
            this.$emit('token-drag', item);
            // this.property = 0
            // item.property = 0
            // item.x = -100
            // item.y = -100
            //
            // // update api with unit location
            // this.updateOfficerToken(item);
        },
        checkLocation: function (that, item) {
            if (that.hitTest(this.$refs.officerGame, '100%')) {
                //location-center
                if (that.hitTest(this.$refs.prop5, '1%')) {
                    this.property = 5
                    item.property = 5;
                    let property = document.getElementById('prop5').getBoundingClientRect()
                    this.calculateLocation(property, that, item);
                } else if (that.hitTest(this.$refs.prop2, '.000001%')) {
                    this.property = 2
                    item.property = 2;
                    let property = document.getElementById('prop2').getBoundingClientRect()
                    this.calculateLocation(property, that, item);
                } else if (that.hitTest(this.$refs.prop3, '.000001%')) {
                    this.property = 3
                    item.property = 3
                    let property = document.getElementById('prop3').getBoundingClientRect()
                    this.calculateLocation(property, that, item);
                } else if (that.hitTest(this.$refs.prop4, '.000001%')) {
                    this.property = 4
                    item.property = 4
                    let property = document.getElementById('prop4').getBoundingClientRect()
                    this.calculateLocation(property, that, item);
                } else if (that.hitTest(this.$refs.detectivecontainer, '100%')) { // todo: change detectivecontainer to investigationcontainer
                    // token added to investigation
                    // return if already in investigation
                    if (item.property == 11) {
                        // console.log('this token is already in investigation')
                    }

                    item.property = 11
                    this.$emit('investigation-update', item)
                } else {
                    gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
                    this.$emit('defense-token-reset', item.number)
                }
            } else {
                gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
                this.$emit('defense-token-reset', item.number)
            }
        },
        calculateLocation(property, unitContext, item) { // todo: how is the function even working? make it: calculateLocation: function() {}let property = document.getElementById('prop4').getBoundingClientRect()
            let unit = unitContext.target.getBoundingClientRect()
            this.locationy = unit.y - property.y - 1;
            this.locationx = unit.x - property.x - 1;
            item.x = this.locationx;
            item.y = this.locationy;

            // update api with unit location
            this.updateOfficerToken(item);
        },
        updateOfficerToken(item) {
            // todo: send event up
            // console.log('item: ', item);
            this.$emit('token-update', item);
        }
    },
    template:
        `
          <div ref="officerGame">
              <div class="upper">      
                <div class='title'>Maps</div> 
                <div class="properties-container">
                    <div v-for="property in properties" v-bind:player-id="(property+1)" :id='"prop" + (property+1)' :ref='"prop" + (property+1)' class="property-container">
                      <div class="property other" v-bind:player-id="(property+1)" :id='"prop" + (property+1)' :ref='"prop" + (property+1)'>
                          <svg v-for="player_id in 4" :key="player_id" :id="'indicator' + (property+1) + '-' + (player_id + 1)" class="indicator" width="6" height="6">
                            <circle cx="3" cy="3" r="2" fill="black" />
                          </svg>
                      </div>
                      <div class="property-label">
                        Player {{property+1}}
                      </div>
                    </div>
                </div>
                <div class="token-container">
                    <div class="title-small">Defend Tokens:</div>
                    <div class="officer-units" style="display:flex;">
                      <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
                        {{unit.number}}
                      </div>
                    </div>
                    <div style="margin: 10px">
                    <div>DEBUG:</div>
                      last dropped<br>
                      property: {{property}}<br>
                      x: {{locationx}}<br>
                      y: {{locationy}}<br>
                    </div>
                </div>
              </div>
              <div class="lower">
                <police-log-component 
                    class="notifications-container"
                    style="border-right: 1px solid black;"
                    :messages="policeLogMessages"
                ></police-log-component>
                <div class="investigation-data-container">
                  <div class="title">Investigation</div>
                    <div>
                        DEBUG: Investigation Token Count {{investigationCount}} <br>
                    </div>
                  <probability-bar-component label="Probability Punish Innocent" :percent=probInnocent></probability-bar-component>
                  <probability-bar-component label="Probability Punish Culprit" :percent=probCulprit></probability-bar-component>
                  <br>
                  <div id="officer-detective-container" ref='detectivecontainer'></div>
    
                </div>
              </div>
          </div>
      `
}