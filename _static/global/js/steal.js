let stealGameComponent = {
    components: {
        'police-log-component': policeLogComponent,
        'probability-bar-component': probabilityBarComponent,
    },
    props: {
        maps: Array,
        groupPlayerId: String,
        playerLocation: Object,
        investigationCount: Number,
        probCulprit: Number,
        probInnocent: Number,
        policeLogMessages: Array,
        mapSize: Number,
        locationLocation: Number,
    },
    data: function () {
        return {
            location: null,
            locationx: 0,
            locationy: 0,
        }
    },
    mounted: function () {
        // this.location = this.$refs.location todo: implement ref for location and all maps retreived by id
        let that = this;
        let selector = '#location'
        Draggable.create(selector, {
            minimumMovement: .01,
            bounds: that.$refs.stealcontainer,
            // bounds: document.getElementById("steal-container"), //todo add ref stuff
            snap: function (val) {
            },
            onDragStart: function () {
                that.locationDragStart(this)
            },
            onDragEnd: function () {
                that.checkLocation(this)
            },
        });

        // this.$nextTick(() => {
        //     this.setLocationLocation();
		// });
        // setTimeout(() => {
        //     this.setLocationLocation();
        // }, 1000)

        // animate to start
        //   if (this.playerLocation && this.playerLocation.map !== null) {
        //     this.calculateLocation(map, 2);
        //
        //       let mapSelector = 'prop' + this.playerLocation.map
        //       let map = document.getElementById(mapSelector).getBoundingClientRect() //todo use refs
        //       let location = this.$refs.location.getBoundingClientRect()
        //       this.locationx = location.x - map.x
        //       this.locationy = location.y - map.y
        //
        //       gsap.to(selector, {left: this.playerLocation.x-15, top: this.playerLocation.y-10})
        //   }
    },
    methods: {
        setLocationLocation: function() {
            debugger;
            console.log(this.locationLocation)
            // animate to the random location:
            if (this.locationLocation === 1) return; // already starts in first steal location

            let start = this.$refs['steallocation1'].getBoundingClientRect();
            let start2 = document.getElementById('steallocation1').getBoundingClientRect();
            let dest = this.$refs['steallocation'+this.locationLocation][0].getBoundingClientRect();

            gsap.to('#location', .5, {x: dest.x-start.x, y: dest.y-start.y});
        },
        locationDragStart: function (that) {
            // check the current location to see if we need to update api
            this.$emit('location-drag', {x: this.locationx, y: this.locationy, map: 0});
        },
        checkLocation: function (that) {
            if (that.hitTest(this.$refs.htarget, '10%')) {
                //location-center
                if (that.hitTest(this.$refs.prop2, '.000001%') && this.groupPlayerId != 2) {
                    let map = document.getElementById('prop2').getBoundingClientRect()
                    this.calculateLocation(map, 2);
                } else if (that.hitTest(this.$refs.prop3, '.000001%') && this.groupPlayerId != 3) {
                    let map = document.getElementById('prop3').getBoundingClientRect()
                    this.calculateLocation(map, 3);
                } else if (that.hitTest(this.$refs.prop4, '.000001%') && this.groupPlayerId != 4) {
                    let map = document.getElementById('prop4').getBoundingClientRect()
                    this.calculateLocation(map, 4);
                } else if (that.hitTest(this.$refs.prop5, '.000001%') && this.groupPlayerId != 5) {
                    let map = document.getElementById('prop5').getBoundingClientRect()
                    this.calculateLocation(map, 5);
                } else {
                    gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
                    this.$emit('location-token-reset') // todo reset location
                }
            } else {
                gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
                this.$emit('location-token-reset') //todo set location
            }
        },
        calculateLocation(map, map_id) {  // prop_id is more like the player_id
            let location = this.$refs.location.getBoundingClientRect()
            this.locationx = location.x - map.x + 2 - 1; // + radius - border
            this.locationy = location.y - map.y + 2 - 1;

            if (0 <= this.locationx &&
                this.locationx <= this.mapSize &&
                0 <= this.locationy &&
                this.locationy <= this.mapSize
            ) {
                this.$emit('location-update', {x: this.locationx, y: this.locationy, map: map_id});
            } else {
                gsap.to('#location', 0.5, {x: 0, y: 0, ease: Back.easeOut});
            }
        },
        indicatorColor(map) {
            if (this.groupPlayerId == map) {
                return 'red'
            }
            else {
                return 'black'
            }
        }
    },
    watch: {
        locationLocation: function() {
            this.setLocationLocation();
        }
    },
    template:
        `
      <div class="steal" style="display:flex; flex-wrap: wrap">
        <div class="game">
            <div id="steal-container" class="upper" ref="stealcontainer">
                <div class='title'>Maps</div> 
                    <div ref='htarget' class="maps-container">
                      <div v-for="map in maps" class="map-container">
                            <div v-bind:class="['map', groupPlayerId==(map+1) ? 'self' : 'other']" v-bind:player-id="(map+1)" :id='"prop" + (map+1)' :ref='"prop" + (map+1)'>
                                <!-- svg indicator id format: map-player-->
                                <svg v-for="player_id in 4" :key="player_id" :id="'indicator' + (map+1) + '-' + (player_id + 1)" class="indicator" width="4" height="4">
                                  <circle cx="2" cy="2" r="2" :fill="indicatorColor(player_id+1)" />
                                </svg>
                            </div>
                            <div class="map-label">{{map+1 == groupPlayerId ? 'You' : 'Player ' + (map+1)}}</div>
                      </div>
                    </div>
                    <div class="token-container">
                      <div class="title-small">
                        Location Token:
                      </div>
                        <div class="steal-locations-container">
                            <div class="steal-token" ref="steallocation1" id="steallocation1">
                                <svg id="location" height="21" width="21">
                                    <line x1="0" y1="0" x2="21" y2="21" style="stroke:red;stroke-width:3;"/>       
                                    <line x1="21" y1="0" x2="0" y2="21" style="stroke:red;stroke-width:3;"/>       
                                        
                                    <circle ref="location" cx="10.5" cy="10.5" r="2" fill="black" />
                                    Sorry, your browser does not support inline SVG.  
                                </svg> 
                            </div>
                            <div v-for="i in 8" class="steal-location" :ref='"steallocation" + (i+1)' :id='"steallocation" + (i+1)'>
                            </div>
                        </div>
                      <br>
                      <div>
                        <div>DEBUG:</div>
                        player id: {{groupPlayerId}} <br>
                        x: {{locationx}}<br> 
                        y: {{locationy}}<br>
                      </div>
                    </div>
              </div>
            <div class="lower" style="display:flex;">
<!--                <police-log-component-->
<!--                    class="notifications-container"-->
<!--                    style="border-right: 1px solid black;"-->
<!--                    :messages="policeLogMessages"-->
<!--                    :player-group-id="groupPlayerId"-->
<!--                ></police-log-component>-->
                <div class="investigation-data-container">
                    <div class="title">Investigating</div>
                    <div>
                        <div class="title-small">Defense Tokens: {{investigationCount}}/9</div>
                        <br>
                        <probability-bar-component label="Probability Punish Innocent" :percent=probInnocent></probability-bar-component>
                        <probability-bar-component label="Probability Punish Culprit" :percent=probCulprit></probability-bar-component>  
                    </div>                  
                </div>
            </div>
        </div>
      </div>
      `
}