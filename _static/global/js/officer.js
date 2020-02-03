let policeLogComponent = {
    props: {
        messages: Array,
        playerGroupId: String
    },
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
                        <div v-for="message in messages" :class="{ selfmessage: message.civilianPunished==playerGroupId }">{{message.civilianPunished}}</div>
                    </div>
                </div>
                <div class="notification-log-column">
                    <div class="header"><div>Map Number</div></div>
                    <div class="content" ref="policeLog2">
                        <div v-for="message in messages" :class="{ selfmessage: message.civilianPunished==playerGroupId }">{{message.mapNumber}}</div>
                    </div>
                </div>
                <div class="notification-log-column">
                    <div class="header"><div>Time (seconds)</div></div>
                    <div class="content" ref="policeLog3">
                        <div v-for="message in messages" :class="{ selfmessage: message.civilianPunished==playerGroupId }">{{message.time}}</div>
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
            <div class="title-small">{{ label }} {{percent}}%</div>
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
        maps: Array,
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
            map: String,
        }
    },
    created: function () {
        this.locationx = '';
        this.locationy = '';
        this.map = '';
    },
    mounted: function () {
        for (let i = 0; i < this.officerUnits.length; i++) {
            let oGame = document.getElementById("officerGame");
            let that = this;
            let drag = Draggable.create("#unit" + i, {
                minimumMovement: .01,
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
            // // update api with unit location
            // this.updateOfficerToken(item);
        },
        checkLocation: function (that, item) {
            if (that.hitTest(this.$refs.officerGame, '100%')) {
                //location-center
                if (that.hitTest(this.$refs.map5, '1%')) {
                    this.map = 5
                    item.map = 5;
                    let map = document.getElementById('map5').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map2, '.000001%')) {
                    this.map = 2
                    item.map = 2;
                    let map = document.getElementById('map2').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map3, '.000001%')) {
                    this.map = 3
                    item.map = 3
                    let map = document.getElementById('map3').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map4, '.000001%')) {
                    this.map = 4
                    item.map = 4
                    let map = document.getElementById('map4').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.investigationcontainer, '100%')) {
                    // already in investigation
                    if (item.map == 11) {
                        return;
                        // console.log('this token is already in investigation')
                    }

                    item.map = 11
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
        calculateLocation: function(map, unitContext, item) { // todo: how is the function even working? make it: calculateLocation: function() {}let map = document.getElementById('map4').getBoundingClientRect()
            let unit = unitContext.target.getBoundingClientRect()
            this.locationy = unit.y - map.y - 1;
            this.locationx = unit.x - map.x - 1;
            item.x = this.locationx;
            item.y = this.locationy;

            // update api with unit location
            this.updateOfficerToken(item);
        },
        updateOfficerToken: function(item) {
            // console.log('item: ', item);
            this.$emit('token-update', item);
        }
    },
    template:
        `
          <div ref="officerGame">
              <div class="upper">      
                <div class='title'>Maps</div> 
                <div class="maps-container">
                    <div v-for="map in maps" v-bind:player-id="(map+1)" :id='"map" + (map+1)' :ref='"map" + (map+1)' class="map-container">
                      <div class="map other" v-bind:player-id="(map+1)" :id='"map" + (map+1)' :ref='"map" + (map+1)'>
                          <svg v-for="player_id in 4" :key="player_id" :id="'indicator' + (map+1) + '-' + (player_id + 1)" class="indicator" width="6" height="6">
                            <circle cx="3" cy="3" r="2" fill="black" />
                          </svg>
                      </div>
                      <div class="map-label">
                        Player {{map+1}}
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
                      map: {{map}}<br>
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
                    :player-group-id="playerGroupId"
                ></police-log-component>
                <div class="investigation-data-container">
                  <div class="title">Investigation</div>
                    <div>
                        DEBUG: Investigation Token Count {{investigationCount}} <br>
                    </div>
                  <probability-bar-component label="Probability Punish Innocent" :percent=probInnocent></probability-bar-component>
                  <probability-bar-component label="Probability Punish Culprit" :percent=probCulprit></probability-bar-component>
                  <br>
                  <div id="officer-investigation-container" ref='investigationcontainer'></div>
    
                </div>
              </div>
          </div>
      `
}