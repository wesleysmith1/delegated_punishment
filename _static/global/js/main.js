let buttonLocationComponent = {
  props: { location: Object,},
  template: '<div><button type="button"">{{location.name}}</button></div>'
}

let propertyComponent = {
  props: { playerId: Number,},
  template: "<div class='property' ref='prop1'>{{playerId}}</div>"
}

let harvestItemsComponent = {
  data: function () {
      return {
        items: ['seed', 'water', 'plow', 'harvest'], // add none here for when nothing has been done or the user just dragged the harvest item successfully
        lastCompleted: null,
        currentStage: 0,
      }
  },
  mounted: function() {
    for (let i = 0; i < this.items.length; i++) {
      let that = this;
      Draggable.create("#" + this.items[i], {
        bounds: document.getElementById("harvestGame"),
        onDragEnd: function() {
          that.checkLocation(this)
        },
      });
    }
  },
  methods: {
    checkLocation: function(that, id) {
      let index = that.target.attributes.index.value;
      if( index==this.currentStage && that.hitTest(this.$refs.htarget, '100%') ){
        // $('#info').text('x: ' + targetX + ', y: ' + targetY );
        var tl = gsap.timeline({onComplete: this.updateHarvestStatus});
        tl.to(that.target, .5, {autoAlpha:0});
        tl.to(that.target, {x:0, y:0});
        // this.updateHarvestStatus()
      } else{
        gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
      }
    },
    updateHarvestStatus() {
      this.currentStage++;

      //todo update api with currentStage



      if (this.currentStage == 4) {
        this.currentStage = 0; 
        gsap.to('#seed, #water, #plow, #harvest', 0.5, {autoAlpha:1});
      }

    }
  },
    // <img src="{% static 'global/water.png' %}" style="height: 100px; width: 100px;"/>
  template: `

    <div id="harvest-container" class="game">
      <div class="upper">
          <div class='harvest-items'>
            <div v-for='(i, index) in items' :id='i' :index='index' :ref='i' class='harvest-item'>
              {{i}}
              <img :src="'/static/global/' + items[index] + '.png'" style="width: 50%; height: 50%"/>
            </div>
          </div>
      </div>
      <div class="lower" ref='htarget'> 
          <div class="harvest-complete-items">
            <div class="harvest-complete-container">
              <div class='harvest-complete-item' v-for='(i, index) in 3'>
                <img :src="'/static/global/' + items[currentStage] + '.png'" style="width: 50%; height: 50%"/>
              </div>
            </div>
            <div class="harvest-complete-container">
              <div class='harvest-complete-item' v-for='(i, index) in 3'>
                <img :src="'/static/global/' + items[currentStage] + '.png'" style="width: 50%; height: 50%"/>
              </div>
            </div>  
          </div>
      </div>
    </div>
  `
}

let stealComponent = {
  components: {
    'property-component': propertyComponent
  },
  props: { properties: Array},
  data: function () {
      return {
        playerId: Number,
        locationx: 0,
        locationy: 0,
      }
  },
  mounted: function() {
    let that = this;
    Draggable.create("#location", {
      minimumMovement: 1,
      bounds: document.getElementById("steal-container"), //todo add ref stuff
      snap: function(val) {
      },
      onDragEnd: function() {
        that.checkLocation(this)
      },
    });
  },
  methods: {
    checkLocation: function(that) {
      if(that.hitTest(this.$refs.htarget, '100%')){
        //location-center
        if(that.hitTest(this.$refs.prop1, '1%')) {
            let property = document.getElementById('prop1').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop2, '1%')) {
            let property = document.getElementById('prop2').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop3, '1%')) {
            let property = document.getElementById('prop3').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop4, '1%')) {
            let property = document.getElementById('prop4').getBoundingClientRect()
            this.calculateLocation(property);
        } else {
            gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref 
        }
        
      } else{
        gsap.to('#locationrect', .1, {fill: 'green'}) // todo make queryselector a vue ref 
      }
    },
    calculateLocation(property) {
      gsap.to('#locationrect', {fill: 'red'})
      let location = this.$refs.location.getBoundingClientRect()
      this.locationx = location.x - property.x + .25
      this.locationy = location.y - property.y + .25 //todo add variable radius here palio
    }
  },
  template: `
    <div id="steal-container">
      <div ref='htarget' class="property-container">
        <div v-for="property in properties" class='property' v-bind:player-id="property" :id='"prop" + property' :ref='"prop" + property'>{{property}}</div>

      </div>
      <div class="location-start">
        <div>
          drag location<br>
          x: {{locationx}}<br> 
          y: {{locationy}}<br>
        </div>
        <svg id="location" height="21" width="21">
          <rect id="locationrect" x="0" y="0" width="21" height="21" style="fill:green;stroke:black;stroke-width:1;fill-opacity:0.1;stroke-opacity:0.9" />
          
          <circle ref="location" cx="10" cy="10" r=".5" fill="black" />
          Sorry, your browser does not support inline SVG.  
        </svg> 
      </div>
    </div>
  `
}

let stealGameComponent = {
  components: {
    'steal-component': stealComponent,

  },
  props: {
    properties: Array,
    playerGroupId: String,

  },
  data: function() {
    return {
      playerId: Number
    }
  },
  template: 
    `
    <div class="steal" style="display:flex; flex-wrap: wrap">
      <div class="game">
          <div class="">
              <steal-component :properties="properties"></steal-component>
          </div>
      </div>
    </div>
    `
}

let policeLogComponent = {
  props: { items: Array,},
  data: function () {
      return {
      }
  },
  template: '<div class="police-log">POLICE LOG PLACEHOLDER</div>'
}

let officerUnitsComponent = {
  components: {
  },
  props: {
    officerUnits: Array,
  },
  data: function() {
    return {
      playerId: Number
    }
  },
  mounted: function() {
    for (var i = 0; i < this.officerUnits.length; i++) {
      let that = this;
      Draggable.create("#unit" + i, {
        bounds: document.getElementById("officerGame"), //todo add ref stuff
        onDragEnd: function() {
          that.checkLocation(this)
        },
        
      });
    }
  },
  methods: {
    checkLocation: function(that) {
      if(that.hitTest(this.$refs.officergame, '100%')){
        //location-center
        if(that.hitTest(this.$refs.prop1, '1%')) {
            let property = document.getElementById('prop1').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop2, '1%')) {
            let property = document.getElementById('prop2').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop3, '1%')) {
            let property = document.getElementById('prop3').getBoundingClientRect()
            this.calculateLocation(property);
        } else if (that.hitTest(this.$refs.prop4, '1%')) {
            let property = document.getElementById('prop4').getBoundingClientRect()
            this.calculateLocation(property);
        } else {
            // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
        
      } else{
        // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
      }
    },
    calculateLocation(property) {
        let location = this.$refs.location.getBoundingClientRect()
        this.locationx = location.x - property.x
        this.locationy = location.y - property.y
    }
  },
  template: 
    `
      <div class="officer-units" style="display:flex; flex-wrap: flex;">
        <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
        </div>
      </div>
    `
}

let policeGameComponent = {
  components: {
    'steal-component': stealComponent,
    'police-log-component': policeLogComponent,
    'property-component': propertyComponent,
    'officer-units-component': officerUnitsComponent
  },
  props: {
    properties: Array,
    officerUnits: Array,
    playerGroupId: String,
  },
  data: function() {
    return {
      playerId: Number,
      locationx: String,
      locationy: String,
      property: String,
      probPunishInnocent: 0,
      probPunishCulprit: 0,
    }
  },
  created: function() {
    this.locationx = '';
    this.locationy = '';
    this.property = '';   
  },
  mounted: function() {
    for (var i = 0; i < this.officerUnits.length; i++) {
      let that = this;
      Draggable.create("#unit" + i, {
        bounds: document.getElementById("officerGame"), //todo add ref stuff
        onDragEnd: function() {
          that.checkLocation(this)
        },
      });
    }
  },
  methods: {
    checkLocation: function(that) {
      if(that.hitTest(this.$refs.officergame, '100%')){
        //location-center
        if(that.hitTest(this.$refs.prop1, '1%')) {
          this.property = 1
            let property = document.getElementById('prop1').getBoundingClientRect()
            this.calculateLocation(property, that);
        } else if (that.hitTest(this.$refs.prop2, '1%')) {
          this.property = 2
            let property = document.getElementById('prop2').getBoundingClientRect()
            this.calculateLocation(property, that);
        } else if (that.hitTest(this.$refs.prop3, '1%')) {
          this.property = 3
            let property = document.getElementById('prop3').getBoundingClientRect()
            this.calculateLocation(property, that);
        } else if (that.hitTest(this.$refs.prop4, '1%')) {
          this.property = 4
            let property = document.getElementById('prop4').getBoundingClientRect()
            this.calculateLocation(property, that);
        } else if (that.hitTest(this.$refs.detectivecontainer, '100%')) {
          this.probPunishCulprit = this.probPunishCulprit + 10
        } else {
            // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
        }
      } else{
        // gsap.to(that.target, 0.5, {x:0, y:0, ease: Back.easeOut});
      }
    },
    calculateLocation(property, unitContext) {
      if (this.probPunishInnocent< 100 ) this.probPunishInnocent = this.probPunishInnocent + 10;
        let unit = unitContext.target.getBoundingClientRect()
        this.locationx = unit.x - property.x
        this.locationy = unit.y - property.y
    }
  },
  template: 
    `
      <div class="officer" style="display:flex;">
        <div class="game" ref="officergame">
            <div class="upper">             
              <div style="display: flex">
                <div class="property" v-for="property in properties" v-bind:player-id="property" :id='"prop" + property' :ref='"prop" + property'>
                  {{property}}
                </div>
              </div>
              <div class="officer-units" style="display:flex;">
                <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" :ref='"unit" + unit'>
                </div>
              </div>
              <div style="margin: 10px">
                last dropped<br>
                property: {{property}}<br>
                x: {{locationx}}<br>
                y: {{locationy}}<br>
              </div>
            </div>
            <div class="lower" style="display:flex;">
              <police-log-component></police-log-component>
              <div class="officer-data">
                Investigation
                <div id="officer-detective-container" ref='detectivecontainer'></div>

                Probability Punish Innocent {{probPunishInnocent}} / 100
                <div class='bar'>
                  <div class="innocent" :style="{'width':(probPunishInnocent+'%')}">
                  </div>
                </div>
                Probability Punish Culprit {{probPunishCulprit}} / 100
                <div class='bar'>
                  <div class="culprit" :style="{'width':(probPunishCulprit+'%')}">
                  </div>
                </div>
                
              </div>
            </div>
        </div>
      </div>
    `
}

let playerHouseComponent = {
  props: { player: Object,},
  data: function () {
      return {
      }
  },
  template: '<div class="house">player"s house</div>'
}